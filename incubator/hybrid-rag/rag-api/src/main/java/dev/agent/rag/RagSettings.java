package dev.agent.rag;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

import java.nio.file.Path;
import java.time.Duration;

@Validated
@ConfigurationProperties("rag")
record RagSettings(
        String encoderUrl, String rerankerUrl, String qdrantUrl,
        @Pattern(regexp = "[a-zA-Z0-9_-]{1,128}") String collection,
        Path corpus, Path ingestLock, boolean rerankEnabled, boolean evaluationEnabled,
        Duration queryTimeout, Duration ingestTimeout, Duration rerankTimeout, @Min(1) int contextBudget
) {}
