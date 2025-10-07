import { Stack, PrimaryButton } from "@fluentui/react";
import { ErrorCircle24Regular } from "@fluentui/react-icons";
import { useTranslation } from "react-i18next";

import styles from "./Answer.module.css";

interface Props {
    error: string;
    onRetry: () => void;
}

export const AnswerError = ({ error, onRetry }: Props) => {
    const { t } = useTranslation();

    // Handle specific error messages
    const getDisplayError = (errorMessage: string) => {
        if (errorMessage.includes("AbortError") && errorMessage.includes("BodyStreamBuffer was aborted")) {
            return t("errors.abortError");
        }
        return errorMessage;
    };

    return (
        <Stack className={styles.answerContainer} verticalAlign="space-between">
            <ErrorCircle24Regular aria-hidden="true" aria-label="Error icon" primaryFill="red" />

            <Stack.Item grow>
                <p className={styles.answerText}>{getDisplayError(error)}</p>
            </Stack.Item>

            <PrimaryButton className={styles.retryButton} onClick={onRetry} text={t("errors.retryButton")} />
        </Stack>
    );
};
