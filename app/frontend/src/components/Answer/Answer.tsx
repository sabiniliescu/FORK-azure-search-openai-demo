import { useMemo, useState } from "react";
import { Stack, IconButton } from "@fluentui/react";
import { useTranslation } from "react-i18next";
import DOMPurify from "dompurify";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

import styles from "./Answer.module.css";
import { ChatAppResponse, getCitationFilePath, SpeechConfig } from "../../api";
import { parseAnswerToHtml } from "./AnswerParser";
import { AnswerIcon } from "./AnswerIcon";
import { SpeechOutputBrowser } from "./SpeechOutputBrowser";
import { SpeechOutputAzure } from "./SpeechOutputAzure";

interface Props {
    answer: ChatAppResponse;
    index: number;
    speechConfig: SpeechConfig;
    isSelected?: boolean;
    isStreaming: boolean;
    onCitationClicked: (filePath: string) => void;
    onThoughtProcessClicked: () => void;
    onSupportingContentClicked: () => void;
    onFollowupQuestionClicked?: (question: string) => void;
    showFollowupQuestions?: boolean;
    showSpeechOutputBrowser?: boolean;
    showSpeechOutputAzure?: boolean;
    showFeedback?: boolean; // New prop to control feedback visibility
    showDeveloperFeatures?: boolean; // New prop to control developer features
}

export const Answer = ({
    answer,
    index,
    speechConfig,
    isSelected,
    isStreaming,
    onCitationClicked,
    onThoughtProcessClicked,
    onSupportingContentClicked,
    onFollowupQuestionClicked,
    showFollowupQuestions,
    showSpeechOutputAzure,
    showSpeechOutputBrowser,
    showFeedback = true, // Default to true for backward compatibility
    showDeveloperFeatures = false // Default to false for backward compatibility
}: Props) => {
    const followupQuestions = answer.context?.followup_questions;
    const parsedAnswer = useMemo(() => parseAnswerToHtml(answer, isStreaming, onCitationClicked), [answer]);
    const { t } = useTranslation();
    const sanitizedAnswerHtml = DOMPurify.sanitize(parsedAnswer.answerHtml);
    // Feedback state
    const [feedback, setFeedback] = useState<string | null>(null);
    const [writtenFeedback, setWrittenFeedback] = useState<string>("");
    const [showWrittenFeedback, setShowWrittenFeedback] = useState(false);
    const [feedbackConfirmation, setFeedbackConfirmation] = useState<string>("");
    const [lastSubmittedFeedback, setLastSubmittedFeedback] = useState<string>("");
    const sendFeedback = (type: "like" | "dislike", text?: string) => {
        setFeedback(type);
        fetch("/api/feedback", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                answerIndex: index,
                feedbackType: type,
                feedbackText: text || null
            })
        })
            .then(() => {
                if (type === "like") {
                    setFeedbackConfirmation("LIKE_SENT");
                } else if (type === "dislike" && text) {
                    setFeedbackConfirmation("DISLIKE_FEEDBACK_SENT");
                    setLastSubmittedFeedback(text);
                } else if (type === "dislike") {
                    setFeedbackConfirmation("DISLIKE_SENT");
                }
            })
            .catch(err => {
                console.error("Feedback error:", err);
                setFeedbackConfirmation("ERROR");
            });
    };
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        const textToCopy = sanitizedAnswerHtml.replace(/<a [^>]*><sup>\d+<\/sup><\/a>|<[^>]+>/g, "");

        navigator.clipboard
            .writeText(textToCopy)
            .then(() => {
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
            })
            .catch(err => console.error("Failed to copy text: ", err));
    };

    return (
        <Stack className={`${styles.answerContainer} ${isSelected && styles.selected}`} verticalAlign="space-between">
            <Stack.Item>
                <Stack horizontal horizontalAlign="space-between">
                    <AnswerIcon />
                    <div>
                        {showDeveloperFeatures && (
                            <>
                                <IconButton
                                    style={{ color: "black" }}
                                    iconProps={{ iconName: "Lightbulb" }}
                                    title={t("tooltips.showThoughtProcess")}
                                    ariaLabel={t("tooltips.showThoughtProcess")}
                                    onClick={() => onThoughtProcessClicked()}
                                    disabled={!answer.context.thoughts?.length || isStreaming}
                                />
                                <IconButton
                                    style={{ color: "black" }}
                                    iconProps={{ iconName: "ClipboardList" }}
                                    title={t("tooltips.showSupportingContent")}
                                    ariaLabel={t("tooltips.showSupportingContent")}
                                    onClick={() => onSupportingContentClicked()}
                                    disabled={!answer.context.data_points || isStreaming}
                                />
                            </>
                        )}
                        {showSpeechOutputAzure && (
                            <SpeechOutputAzure answer={sanitizedAnswerHtml} index={index} speechConfig={speechConfig} isStreaming={isStreaming} />
                        )}
                        {showSpeechOutputBrowser && <SpeechOutputBrowser answer={sanitizedAnswerHtml} />}
                    </div>
                </Stack>
            </Stack.Item>

            <Stack.Item grow>
                <div className={styles.answerText}>
                    <ReactMarkdown
                        children={sanitizedAnswerHtml}
                        rehypePlugins={[rehypeRaw]}
                        remarkPlugins={[remarkGfm]}
                        components={{
                            a: (props: any) => (
                                <a href={props.href} target="_blank" rel="noopener noreferrer">
                                    {props.children}
                                </a>
                            )
                        }}
                    />
                </div>
            </Stack.Item>

            {!!parsedAnswer.citations.length && (
                <Stack.Item>
                    <Stack horizontal wrap tokens={{ childrenGap: 5 }}>
                        <span className={styles.citationLearnMore}>{t("citationWithColon")}</span>
                        {parsedAnswer.citations.map((x, i) => {
                            const path = getCitationFilePath(x);
                            return (
                                <a key={i} className={styles.citation} title={x} onClick={() => onCitationClicked(path)}>
                                    {`${++i}. ${x}`}
                                </a>
                            );
                        })}
                    </Stack>
                </Stack.Item>
            )}

            {!!followupQuestions?.length && showFollowupQuestions && onFollowupQuestionClicked && (
                <Stack.Item>
                    <Stack horizontal wrap className={`${!!parsedAnswer.citations.length ? styles.followupQuestionsList : ""}`} tokens={{ childrenGap: 6 }}>
                        <span className={styles.followupQuestionLearnMore}>{t("followupQuestions")}</span>
                        {followupQuestions.map((x, i) => {
                            return (
                                <a key={i} className={styles.followupQuestion} title={x} onClick={() => onFollowupQuestionClicked(x)}>
                                    {`${x}`}
                                </a>
                            );
                        })}
                    </Stack>
                </Stack.Item>
            )}

            {/* Feedback box bottom left - conditional display */}
            <Stack.Item>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", justifyContent: "flex-start", marginTop: 16 }}>
                    <div style={{ display: "flex", flexDirection: "row", alignItems: "center" }}>
                        {/* Copy button and conditional Like/Dislike buttons */}
                        <div style={{ display: "flex", flexDirection: "row", alignItems: "center" }}>
                            <IconButton
                                style={{ color: "black" }}
                                iconProps={{ iconName: copied ? "CheckMark" : "Copy" }}
                                title={copied ? t("tooltips.copied") : t("tooltips.copy")}
                                ariaLabel={copied ? t("tooltips.copied") : t("tooltips.copy")}
                                onClick={handleCopy}
                            />
                            {showFeedback && (
                                <>
                                    <IconButton
                                        style={{ color: feedback === "like" ? "green" : "black" }}
                                        iconProps={{ iconName: "Like" }}
                                        title="Like"
                                        ariaLabel="Like"
                                        onClick={() => {
                                            setShowWrittenFeedback(false);
                                            sendFeedback("like");
                                        }}
                                    />
                                    <IconButton
                                        style={{ color: feedback === "dislike" ? "red" : "black" }}
                                        iconProps={{ iconName: "Dislike" }}
                                        title="Dislike"
                                        ariaLabel="Dislike"
                                        onClick={() => {
                                            setShowWrittenFeedback(true);
                                            setFeedback("dislike");
                                            sendFeedback("dislike");
                                        }}
                                    />
                                </>
                            )}
                        </div>
                        {/* Feedback input box to the right - only when feedback is enabled */}
                        {showFeedback && showWrittenFeedback && feedback === "dislike" && (
                            <div style={{ marginLeft: 12, marginTop: 0, display: "flex", alignItems: "center" }}>
                                <input
                                    type="text"
                                    value={writtenFeedback}
                                    onChange={e => setWrittenFeedback(e.target.value)}
                                    placeholder="Lasă un feedback..."
                                    style={{ width: "200px", marginRight: 8 }}
                                    onKeyDown={e => {
                                        if (e.key === "Enter" && writtenFeedback.trim()) {
                                            sendFeedback("dislike", writtenFeedback);
                                            setShowWrittenFeedback(false);
                                            setWrittenFeedback("");
                                        }
                                    }}
                                />
                                <IconButton
                                    iconProps={{ iconName: "Send" }}
                                    title="Trimite feedback"
                                    ariaLabel="Trimite feedback"
                                    onClick={() => {
                                        sendFeedback("dislike", writtenFeedback);
                                        setShowWrittenFeedback(false);
                                        setWrittenFeedback("");
                                    }}
                                />
                            </div>
                        )}
                    </div>
                    {/* Confirmation messages below buttons/input - only when feedback is enabled */}
                    {showFeedback && (
                        <div style={{ marginTop: 8, display: "flex", flexDirection: "column" }}>
                            {feedbackConfirmation === "DISLIKE_SENT" && <div style={{ color: "red", fontWeight: "bold" }}>Dislike trimis!</div>}
                            {feedbackConfirmation === "LIKE_SENT" && <div style={{ color: "green", fontWeight: "bold" }}>Like trimis!</div>}
                            {feedbackConfirmation === "DISLIKE_FEEDBACK_SENT" && (
                                <>
                                    <div style={{ color: "red", fontWeight: "bold" }}>Dislike și feedback trimis!</div>
                                    {lastSubmittedFeedback && (
                                        <div style={{ marginTop: 4, fontStyle: "italic", color: "red", fontWeight: "normal" }}>{lastSubmittedFeedback}</div>
                                    )}
                                </>
                            )}
                            {feedbackConfirmation === "ERROR" && <div style={{ color: "orange", fontWeight: "bold" }}>A apărut o eroare la trimitere!</div>}
                        </div>
                    )}
                    {/* Speech output remains below */}
                    <div style={{ marginTop: 8 }}>
                        {showSpeechOutputAzure && (
                            <SpeechOutputAzure answer={sanitizedAnswerHtml} index={index} speechConfig={speechConfig} isStreaming={isStreaming} />
                        )}
                        {showSpeechOutputBrowser && <SpeechOutputBrowser answer={sanitizedAnswerHtml} />}
                    </div>
                </div>
            </Stack.Item>
        </Stack>
    );
};
