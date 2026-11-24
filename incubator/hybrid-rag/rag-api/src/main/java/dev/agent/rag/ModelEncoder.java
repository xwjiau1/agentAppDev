package dev.agent.rag;

import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

import java.util.List;
import java.util.Map;
import java.util.Objects;

import static dev.agent.rag.Contracts.*;

record ModelEncoder(RestClient client) implements EncoderClient {
    private record Health(String modelSignature) {}
    private record Batch(String modelSignature, List<Embedding> items) {}

    @Override
    public String signature() {
        try {
            Health health = client.get().uri("/health/ready").retrieve().body(Health.class);
            if (health == null || health.modelSignature() == null || health.modelSignature().isBlank()) {
                throw new RagFailure(502, "Encoder returned an invalid model signature");
            }
            return health.modelSignature();
        } catch (RestClientException failure) {
            throw new RagFailure(503, "Encoder readiness check failed", failure);
        }
    }

    @Override
    public List<Embedding> encode(List<String> texts, String expectedSignature, String requestId) {
        try {
            Batch response = client.post().uri("/encode").header("X-Request-ID", requestId)
                    .body(Map.of("texts", texts)).retrieve().body(Batch.class);
            if (response == null || !expectedSignature.equals(response.modelSignature()) || response.items() == null
                    || response.items().size() != texts.size() || response.items().stream().anyMatch(Objects::isNull)) {
                throw new RagFailure(502, "Encoder returned an incompatible batch");
            }
            return response.items();
        } catch (RestClientResponseException failure) {
            if (failure.getStatusCode().value() == 422) {
                throw new RagFailure(422, "Text exceeds the encoder input constraints", failure);
            }
            throw new RagFailure(503, "Encoder request failed", failure);
        } catch (RestClientException failure) {
            throw new RagFailure(503, "Encoder request failed", failure);
        }
    }
}
