from collections.abc import Awaitable, AsyncGenerator
from typing import Any, Optional, Union, cast
import time
import sys
from datetime import datetime

from azure.search.documents.agent.aio import KnowledgeAgentRetrievalClient
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorQuery
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)

from approaches.approach import DataPoints, ExtraInfo, ThoughtStep
from approaches.chatapproach import ChatApproach
from approaches.promptmanager import PromptManager
from core.authentication import AuthenticationHelper


class ChatReadRetrieveReadApproach(ChatApproach):
    def print_feedback(self, feedback_data: dict[str, Any]):
        action = feedback_data.get('feedbackType')
        text = feedback_data.get('feedbackText')
        print(f"[FEEDBACK] Action: {action}")
        if text:
            print(f"[FEEDBACK] Text: {text}")

    def _get_timestamp(self):
        """Get current timestamp in HH:MM:SS format"""
        return datetime.now().strftime("%H:%M:%S")

    def _log_timing(self, message: str, duration_s: float = None):
        """Log timing information with timestamp"""
        if not self.enable_debug_logging:
            return
            
        timestamp = self._get_timestamp()
        if duration_s is not None:
            print(f"[TIMING {timestamp}] {message}: {duration_s:.3f} s")
        else:
            print(f"[TIMING {timestamp}] {message}")

    def _analyze_performance_issues(self, messages: list, response_token_limit: int, temperature: float):
        """Analyze potential performance issues based on request parameters"""
        if not self.enable_debug_logging:
            return
            
        total_chars = sum(len(str(msg.get('content', ''))) for msg in messages if isinstance(msg.get('content'), str))
        
        issues = []
        if total_chars > 50000:
            issues.append(f"Very large input ({total_chars} chars) - may cause slow response")
        if response_token_limit > 2000:
            issues.append(f"High token limit ({response_token_limit}) - longer generation time expected")
        if len(messages) > 20:
            issues.append(f"Many messages ({len(messages)}) - complex conversation context")
        if temperature > 0.7:
            issues.append(f"High temperature ({temperature}) - may increase response time")
        
        if issues:
            self._log_timing("⚠️  POTENTIAL PERFORMANCE ISSUES:")
            for issue in issues:
                self._log_timing(f"   - {issue}")
        else:
            self._log_timing("✅ Request parameters look normal for performance")

    """
    A multi-step approach that first uses OpenAI to turn the user's question into a search query,
    then uses Azure AI Search to retrieve relevant documents, and then sends the conversation history,
    original user question, and search results to OpenAI to generate a response.
    """

    def __init__(
        self,
        *,
        search_client: SearchClient,
        search_index_name: str,
        agent_model: Optional[str],
        agent_deployment: Optional[str],
        agent_client: KnowledgeAgentRetrievalClient,
        auth_helper: AuthenticationHelper,
        openai_client: AsyncOpenAI,
        chatgpt_model: str,
        chatgpt_deployment: Optional[str],  # Not needed for non-Azure OpenAI
        embedding_deployment: Optional[str],  # Not needed for non-Azure OpenAI or for retrieval_mode="text"
        embedding_model: str,
        embedding_dimensions: int,
        embedding_field: str,
        sourcepage_field: str,
        content_field: str,
        query_language: str,
        query_speller: str,
        prompt_manager: PromptManager,
        reasoning_effort: Optional[str] = None,
        enable_debug_logging: bool = False,  # New parameter for controlling debug logging
    ):
        super().__init__(
            search_client=search_client,
            openai_client=openai_client,
            auth_helper=auth_helper,
            query_language=query_language,
            query_speller=query_speller,
            embedding_deployment=embedding_deployment,
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
            embedding_field=embedding_field,
            openai_host=None,
            vision_endpoint=None,
            vision_token_provider=None,
            prompt_manager=prompt_manager,
            reasoning_effort=reasoning_effort,
        )
        self.search_index_name = search_index_name
        self.agent_model = agent_model
        self.agent_deployment = agent_deployment
        self.agent_client = agent_client
        self.openai_client = openai_client
        self.chatgpt_model = chatgpt_model
        self.chatgpt_deployment = chatgpt_deployment
        self.embedding_deployment = embedding_deployment
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions
        self.embedding_field = embedding_field
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field
        self.prompt_manager = prompt_manager
        self.query_rewrite_prompt = self.prompt_manager.load_prompt("chat_query_rewrite.prompty")
        self.query_rewrite_tools = self.prompt_manager.load_tools("chat_query_rewrite_tools.json")
        self.answer_prompt = self.prompt_manager.load_prompt("chat_answer_question.prompty")
        self.reasoning_effort = reasoning_effort
        self.include_token_usage = True
        self.enable_debug_logging = enable_debug_logging  # Store the debug logging preference
        import logging
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run_until_final_call(
        self,
        messages: list[ChatCompletionMessageParam],
        overrides: dict[str, Any],
        auth_claims: dict[str, Any],
        should_stream: bool = False,
    ) -> tuple[ExtraInfo, Union[Awaitable[ChatCompletion], Awaitable[AsyncStream[ChatCompletionChunk]]]]:
        start_time = time.time()
        
        # Print feedback if present in overrides
        feedback_data = overrides.get('feedback_data')
        if feedback_data:
            self.print_feedback(feedback_data)
        
        use_agentic_retrieval = True if overrides.get("use_agentic_retrieval") else False
        self._log_timing(f"run_until_final_call: start use_agentic_retrieval={use_agentic_retrieval}")
        
        original_user_query = messages[-1]["content"]

        reasoning_model_support = self.GPT_REASONING_MODELS.get(self.chatgpt_model)
        if reasoning_model_support and (not reasoning_model_support.streaming and should_stream):
            raise Exception(
                f"{self.chatgpt_model} does not support streaming. Please use a different model or disable streaming."
            )
        
        retrieval_start_time = time.time()
        if use_agentic_retrieval:
            extra_info = await self.run_agentic_retrieval_approach(messages, overrides, auth_claims)
        else:
            extra_info = await self.run_search_approach(messages, overrides, auth_claims)
        retrieval_duration = time.time() - retrieval_start_time
        self._log_timing("Retrieval approach took", retrieval_duration)

        prompt_start_time = time.time()
        # print(f"[DEBUG] text_sources being sent to prompt: {extra_info.data_points.text[:3]}", file=sys.stdout)
        messages = self.prompt_manager.render_prompt(
            self.answer_prompt,
            self.get_system_prompt_variables(overrides.get("prompt_template"))
            | {
                "include_follow_up_questions": bool(overrides.get("suggest_followup_questions")),
                "past_messages": messages[:-1],
                "user_query": original_user_query,
                "text_sources": extra_info.data_points.text,
            },
        )
        prompt_duration = time.time() - prompt_start_time
        self._log_timing("Answer prompt rendering took", prompt_duration)
        
        # Debug: Print final message being sent to AI
        final_message = messages[-1] if messages else None
        if final_message and isinstance(final_message.get('content'), str):
            content = final_message['content']
            sources_start = content.find("Sources:")
            if sources_start != -1:
                sources_section = content[sources_start:sources_start+500]
                # print(f"[DEBUG] Sources section in prompt: {sources_section}", file=sys.stdout)

        chat_coroutine = cast(
            Union[Awaitable[ChatCompletion], Awaitable[AsyncStream[ChatCompletionChunk]]],
            self.create_chat_completion(
                self.chatgpt_deployment,
                self.chatgpt_model,
                messages,
                overrides,
                self.get_response_token_limit(self.chatgpt_model, 3000),
                should_stream,
            ),
        )
        extra_info.thoughts.append(
            self.format_thought_step_for_chatcompletion(
                title="Prompt to generate answer",
                messages=messages,
                overrides=overrides,
                model=self.chatgpt_model,
                deployment=self.chatgpt_deployment,
                usage=None,
            )
        )
        
        total_duration = time.time() - start_time
        self._log_timing("run_until_final_call (pre OpenAI send) took", total_duration)
        
        return (extra_info, chat_coroutine)

    async def run_without_streaming(
        self,
        messages: list[ChatCompletionMessageParam],
        overrides: dict[str, Any],
        auth_claims: dict[str, Any],
        session_state: Any = None,
    ) -> dict[str, Any]:
        extra_info, chat_coroutine = await self.run_until_final_call(
            messages, overrides, auth_claims, should_stream=False
        )
        
        # Debug info about the request being sent to OpenAI
        self._log_timing("Starting OpenAI call with the following details:")
        self._log_timing(f"Model: {self.chatgpt_model}")
        self._log_timing(f"Deployment: {self.chatgpt_deployment}")
        self._log_timing(f"Temperature: {overrides.get('temperature', 0.3)}")
        self._log_timing(f"Max tokens: {self.get_response_token_limit(self.chatgpt_model, 3000)}")
        
        # Count tokens in messages (approximate)
        total_message_length = sum(len(str(msg.get('content', ''))) for msg in messages if isinstance(msg.get('content'), str))
        self._log_timing(f"Approximate input character count: {total_message_length}")
        self._log_timing(f"Number of messages: {len(messages)}")
        
        # Time the actual OpenAI call
        openai_start_time = time.time()
        self._log_timing("OpenAI API call starting now...")
        
        chat_completion_response: ChatCompletion = await cast(Awaitable[ChatCompletion], chat_coroutine)
        
        openai_duration = time.time() - openai_start_time
        self._log_timing("OpenAI answer generation took", openai_duration)
        
        # Debug response details
        if chat_completion_response.usage:
            usage = chat_completion_response.usage
            self._log_timing(f"Token usage - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")
            if hasattr(usage, 'prompt_tokens_details') and usage.prompt_tokens_details:
                self._log_timing(f"Prompt token details: {usage.prompt_tokens_details}")
            if hasattr(usage, 'completion_tokens_details') and usage.completion_tokens_details:
                self._log_timing(f"Completion token details: {usage.completion_tokens_details}")
        
        content_length = len(chat_completion_response.choices[0].message.content or "")
        self._log_timing(f"Response content length: {content_length} characters")
        
        if hasattr(chat_completion_response, 'system_fingerprint'):
            self._log_timing(f"System fingerprint: {chat_completion_response.system_fingerprint}")
        
        content = chat_completion_response.choices[0].message.content
        role = chat_completion_response.choices[0].message.role
        if overrides.get("suggest_followup_questions"):
            content, followup_questions = self.extract_followup_questions(content)
            extra_info.followup_questions = followup_questions
        # Assume last thought is for generating answer
        if self.include_token_usage and extra_info.thoughts and chat_completion_response.usage:
            extra_info.thoughts[-1].update_token_usage(chat_completion_response.usage)
        chat_app_response = {
            "message": {"content": content, "role": role},
            "context": extra_info,
            "session_state": session_state,
        }
        return chat_app_response

    async def run_with_streaming(
        self,
        messages: list[ChatCompletionMessageParam],
        overrides: dict[str, Any],
        auth_claims: dict[str, Any],
        session_state: Any = None,
    ) -> AsyncGenerator[dict, None]:
        extra_info, chat_coroutine = await self.run_until_final_call(
            messages, overrides, auth_claims, should_stream=True
        )
        chat_coroutine = cast(Awaitable[AsyncStream[ChatCompletionChunk]], chat_coroutine)
        yield {"delta": {"role": "assistant"}, "context": extra_info, "session_state": session_state}

        # Debug info for streaming
        self._log_timing("Starting OpenAI streaming call with the following details:")
        self._log_timing(f"Model: {self.chatgpt_model}")
        self._log_timing(f"Deployment: {self.chatgpt_deployment}")
        self._log_timing(f"Temperature: {overrides.get('temperature', 0.3)}")
        
        total_message_length = sum(len(str(msg.get('content', ''))) for msg in messages if isinstance(msg.get('content'), str))
        self._log_timing(f"Approximate input character count: {total_message_length}")
        self._log_timing(f"Number of messages: {len(messages)}")

        # Time the streaming response
        streaming_start_time = time.time()
        first_token_received = False
        token_count = 0
        chunk_count = 0
        
        self._log_timing("OpenAI streaming API call starting now...")
        
        followup_questions_started = False
        followup_content = ""
        async for event_chunk in await chat_coroutine:
            chunk_count += 1
            
            if not first_token_received:
                first_token_time = time.time() - streaming_start_time
                self._log_timing("OpenAI first token received after", first_token_time)
                first_token_received = True
                
            # "2023-07-01-preview" API version has a bug where first response has empty choices
            event = event_chunk.model_dump()  # Convert pydantic model to dict
            if event["choices"]:
                # Count tokens (approximate)
                content = event["choices"][0]["delta"].get("content")
                if content:
                    token_count += len(content.split())
                
                # No usage during streaming
                completion = {
                    "delta": {
                        "content": content,
                        "role": event["choices"][0]["delta"]["role"],
                    }
                }
                # if event contains << and not >>, it is start of follow-up question, truncate
                content = content or ""  # content may either not exist in delta, or explicitly be None
                if overrides.get("suggest_followup_questions") and "<<" in content:
                    followup_questions_started = True
                    earlier_content = content[: content.index("<<")]
                    if earlier_content:
                        completion["delta"]["content"] = earlier_content
                        yield completion
                    followup_content += content[content.index("<<") :]
                elif followup_questions_started:
                    followup_content += content
                else:
                    yield completion
            else:
                # Final chunk at end of streaming should contain usage
                # https://cookbook.openai.com/examples/how_to_stream_completions#4-how-to-get-token-usage-data-for-streamed-chat-completion-response
                if event_chunk.usage and extra_info.thoughts and self.include_token_usage:
                    extra_info.thoughts[-1].update_token_usage(event_chunk.usage)
                    yield {"delta": {"role": "assistant"}, "context": extra_info, "session_state": session_state}

        streaming_total_duration = time.time() - streaming_start_time
        self._log_timing("OpenAI streaming response total took", streaming_total_duration)
        self._log_timing(f"Total chunks received: {chunk_count}")
        self._log_timing(f"Approximate tokens generated: {token_count}")
        
        if token_count > 0 and streaming_total_duration > 0:
            tokens_per_second = token_count / streaming_total_duration
            self._log_timing(f"Approximate tokens per second: {tokens_per_second:.2f}")
        
        if followup_content:
            _, followup_questions = self.extract_followup_questions(followup_content)
            yield {
                "delta": {"role": "assistant"},
                "context": {"context": extra_info, "followup_questions": followup_questions},
            }

    async def run_search_approach(
        self, messages: list[ChatCompletionMessageParam], overrides: dict[str, Any], auth_claims: dict[str, Any]
    ):
        start_time = time.time()
        self._log_timing("run_search_approach: start")
        
        use_text_search = overrides.get("retrieval_mode") in ["text", "hybrid", None]
        use_vector_search = overrides.get("retrieval_mode") in ["vectors", "hybrid", None]
        use_semantic_ranker = True if overrides.get("semantic_ranker") else False
        use_semantic_captions = True if overrides.get("semantic_captions") else False
        use_query_rewriting = True if overrides.get("query_rewriting") else False
        top = overrides.get("top", 3)
        minimum_search_score = overrides.get("minimum_search_score", 0.0)
        minimum_reranker_score = overrides.get("minimum_reranker_score", 0.0)
        search_index_filter = self.build_filter(overrides, auth_claims)

        original_user_query = messages[-1]["content"]
        if not isinstance(original_user_query, str):
            raise ValueError("The most recent message content must be a string.")

        query_messages = self.prompt_manager.render_prompt(
            self.query_rewrite_prompt, {"user_query": original_user_query, "past_messages": messages[:-1]}
        )
        tools: list[ChatCompletionToolParam] = self.query_rewrite_tools

        # STEP 1: Generate an optimized keyword search query based on the chat history and the last question
        query_generation_start = time.time()
        chat_completion = cast(
            ChatCompletion,
            await self.create_chat_completion(
                self.chatgpt_deployment,
                self.chatgpt_model,
                messages=query_messages,
                overrides=overrides,
                response_token_limit=self.get_response_token_limit(
                    self.chatgpt_model, 100
                ),  # Setting too low risks malformed JSON, setting too high may affect performance
                temperature=0.0,  # Minimize creativity for search query generation
                tools=tools,
                reasoning_effort="low",  # Minimize reasoning for search query generation
            ),
        )
        query_generation_duration = (time.time() - query_generation_start)
        self._log_timing("Query generation took", query_generation_duration)

        query_text = self.get_search_query(chat_completion, original_user_query)

        # STEP 2: Retrieve relevant documents from the search index with the GPT optimized query

        # If retrieval mode includes vectors, compute an embedding for the query
        vectors: list[VectorQuery] = []
        if use_vector_search:
            embedding_start = time.time()
            vectors.append(await self.compute_text_embedding(query_text))
            embedding_duration = time.time() - embedding_start
            self._log_timing("Text embedding computation took", embedding_duration)

        search_start = time.time()
        results = await self.search(
            top,
            query_text,
            search_index_filter,
            vectors,
            use_text_search,
            use_vector_search,
            use_semantic_ranker,
            use_semantic_captions,
            minimum_search_score,
            minimum_reranker_score,
            use_query_rewriting,
        )
        search_duration = time.time() - search_start
        self._log_timing(f"Search call took", search_duration)
        self._log_timing(f"Search returned {len(results)} docs")

        # STEP 3: Generate a contextual and content specific answer using the search results and chat history
        sources_start = time.time()
        
        # Creează mapping-ul de linkuri pentru optimizarea streaming-ului
        link_mapping = self.create_link_mapping(results)
        # print(f"[DEBUG] Search approach link_mapping: {link_mapping}", file=sys.stdout)
        text_sources = self.get_sources_content(results, use_semantic_captions, use_image_citation=False, link_mapping=link_mapping)
        
        sources_duration = time.time() - sources_start
        self._log_timing("Search source content assembly took", sources_duration)

        extra_info = ExtraInfo(
            DataPoints(text=text_sources),
            thoughts=[
                self.format_thought_step_for_chatcompletion(
                    title="Prompt to generate search query",
                    messages=query_messages,
                    overrides=overrides,
                    model=self.chatgpt_model,
                    deployment=self.chatgpt_deployment,
                    usage=chat_completion.usage,
                    reasoning_effort="low",
                ),
                ThoughtStep(
                    "Search using generated search query",
                    query_text,
                    {
                        "use_semantic_captions": use_semantic_captions,
                        "use_semantic_ranker": use_semantic_ranker,
                        "use_query_rewriting": use_query_rewriting,
                        "top": top,
                        "filter": search_index_filter,
                        "use_vector_search": use_vector_search,
                        "use_text_search": use_text_search,
                    },
                ),
                ThoughtStep(
                    "Search results",
                    [result.serialize_for_results() for result in results],
                ),
            ],
            link_mapping=link_mapping  # Adaugă mapping-ul în extra_info
        )
        # print(f"[DEBUG] Search extra_info.link_mapping: {extra_info.link_mapping}", file=sys.stdout)
        
        total_duration = time.time() - start_time
        self._log_timing("run_search_approach total took", total_duration)
        
        return extra_info

    async def run_agentic_retrieval_approach(
        self,
        messages: list[ChatCompletionMessageParam],
        overrides: dict[str, Any],
        auth_claims: dict[str, Any],
    ):
        start_time = time.time()
        self._log_timing("run_agentic_retrieval_approach: start")
        
        minimum_reranker_score = overrides.get("minimum_reranker_score", 0)
        search_index_filter = self.build_filter(overrides, auth_claims)
        top = overrides.get("top", 3)
        max_subqueries = overrides.get("max_subqueries", 10)
        results_merge_strategy = overrides.get("results_merge_strategy", "interleaved")
        # 50 is the amount of documents that the reranker can process per query
        max_docs_for_reranker = max_subqueries * 50

        agentic_start = time.time()
        response, results = await self.run_agentic_retrieval(
            messages=messages,
            agent_client=self.agent_client,
            search_index_name=self.search_index_name,
            top=top,
            filter_add_on=search_index_filter,
            minimum_reranker_score=minimum_reranker_score,
            max_docs_for_reranker=max_docs_for_reranker,
            results_merge_strategy=results_merge_strategy,
        )
        agentic_duration = time.time() - agentic_start
        self._log_timing(f"Agentic retrieval call took", agentic_duration)
        self._log_timing(f"Agentic retrieval returned {len(results)} docs")

        sources_start = time.time()
        
        # Creează mapping-ul de linkuri pentru optimizarea streaming-ului
        link_mapping = self.create_link_mapping(results)
        # print(f"[DEBUG] Agentic approach link_mapping: {link_mapping}", file=sys.stdout)
        text_sources = self.get_sources_content(results, use_semantic_captions=False, use_image_citation=False, link_mapping=link_mapping)
        
        sources_duration = time.time() - sources_start
        self._log_timing("Agentic source content assembly took", sources_duration)

        extra_info = ExtraInfo(
            DataPoints(text=text_sources),
            thoughts=[
                ThoughtStep(
                    "Use agentic retrieval",
                    messages,
                    {
                        "reranker_threshold": minimum_reranker_score,
                        "max_docs_for_reranker": max_docs_for_reranker,
                        "results_merge_strategy": results_merge_strategy,
                        "filter": search_index_filter,
                    },
                ),
                ThoughtStep(
                    f"Agentic retrieval results (top {top})",
                    [result.serialize_for_results() for result in results],
                    {
                        "query_plan": (
                            [activity.as_dict() for activity in response.activity] if response.activity else None
                        ),
                        "model": self.agent_model,
                        "deployment": self.agent_deployment,
                    },
                ),
            ],
            link_mapping=link_mapping  # Adaugă mapping-ul în extra_info
        )
        # print(f"[DEBUG] Agentic extra_info.link_mapping: {extra_info.link_mapping}", file=sys.stdout)
        
        total_duration = time.time() - start_time
        self._log_timing("run_agentic_retrieval_approach total took", total_duration)
        
        # print("DEBUG extra_info:", extra_info)
        # print("DEBUG extra_info.data_points:", extra_info.data_points)
        # print("DEBUG extra_info.thoughts:", extra_info.thoughts)
        return extra_info

    def create_chat_completion(
        self,
        chatgpt_deployment: Optional[str],
        chatgpt_model: str,
        messages: list[ChatCompletionMessageParam],
        overrides: dict[str, Any],
        response_token_limit: int,
        should_stream: bool = False,
        tools: Optional[list[ChatCompletionToolParam]] = None,
        temperature: Optional[float] = None,
        n: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
    ):
        # Log detailed parameters before the OpenAI call
        self._log_timing("=== OpenAI API Call Parameters ===")
        self._log_timing(f"Model: {chatgpt_model}")
        self._log_timing(f"Deployment: {chatgpt_deployment}")
        self._log_timing(f"Should stream: {should_stream}")
        self._log_timing(f"Response token limit: {response_token_limit}")
        self._log_timing(f"Temperature override: {temperature}")
        self._log_timing(f"Temperature from overrides: {overrides.get('temperature', 'not set')}")
        self._log_timing(f"Seed: {overrides.get('seed', 'not set')}")
        self._log_timing(f"N: {n}")
        self._log_timing(f"Reasoning effort: {reasoning_effort}")
        self._log_timing(f"Tools provided: {len(tools) if tools else 0}")
        
        # Count and log message details
        total_chars = 0
        for i, msg in enumerate(messages):
            content = msg.get('content', '')
            if isinstance(content, str):
                char_count = len(content)
                total_chars += char_count
                self._log_timing(f"Message {i+1} ({msg.get('role', 'unknown')}): {char_count} chars")
            elif isinstance(content, list):
                # Handle multimodal content
                text_chars = sum(len(item.get('text', '')) for item in content if item.get('type') == 'text')
                total_chars += text_chars
                self._log_timing(f"Message {i+1} ({msg.get('role', 'unknown')}): {text_chars} text chars, {len(content)} items")
        
        self._log_timing(f"Total message character count: {total_chars}")
        self._log_timing(f"Total messages: {len(messages)}")
        
        # Analyze potential performance issues
        final_temperature = temperature or overrides.get('temperature', 0.3)
        self._analyze_performance_issues(messages, response_token_limit, final_temperature)
        
        self._log_timing("================================")
        
        # Call the parent implementation
        return super().create_chat_completion(
            chatgpt_deployment=chatgpt_deployment,
            chatgpt_model=chatgpt_model,
            messages=messages,
            overrides=overrides,
            response_token_limit=response_token_limit,
            should_stream=should_stream,
            tools=tools,
            temperature=temperature,
            n=n,
            reasoning_effort=reasoning_effort,
        )
