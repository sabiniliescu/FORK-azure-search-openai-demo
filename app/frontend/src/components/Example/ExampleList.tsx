import { Example } from "./Example";
import { useTranslation } from "react-i18next";
import { useMemo } from "react";

import styles from "./Example.module.css";

interface Props {
    onExampleClicked: (value: string) => void;
    useGPT4V?: boolean;
}

export const ExampleList = ({ onExampleClicked, useGPT4V }: Props) => {
    const { t } = useTranslation();

    // Helper: pick a random item from an array
    const pickRandom = (arr: string[]): string => arr[Math.floor(Math.random() * arr.length)];

    // Helper: get variants for a base i18n key if provided, else fall back to the base string
    const getRandomizedExamples = (baseNs: string): string[] => {
        const indices = ["1", "2", "3"]; // three boxes

        return indices.map(idx => {
            // Try to load array variants (e.g., defaultExamples.1Variants)
            const variantsKey = `${baseNs}.${idx}Variants`;
            const variants = t(variantsKey, { returnObjects: true }) as unknown;

            if (Array.isArray(variants) && variants.length > 0) {
                // Use a random variant if an array is provided
                return pickRandom(variants as string[]);
            }

            // Fallback to single string (e.g., defaultExamples.1)
            return t(`${baseNs}.${idx}`) as string;
        });
    };

    const examples = useMemo(
        () => (useGPT4V ? getRandomizedExamples("gpt4vExamples") : getRandomizedExamples("defaultExamples")),
        [useGPT4V]
    );

    return (
        <ul className={styles.examplesNavList}>
            {examples.map((question, i) => (
                <li key={i}>
                    <Example text={question} value={question} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};
