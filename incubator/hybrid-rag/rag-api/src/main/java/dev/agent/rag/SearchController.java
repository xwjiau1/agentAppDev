package dev.agent.rag;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;
import java.util.UUID;

import static dev.agent.rag.Contracts.Mode;

@RestController
class SearchController {
    private static final Logger LOG = LoggerFactory.getLogger(SearchController.class);
    private final SearchService service;
    private final RagSettings settings;

    SearchController(SearchService service, RagSettings settings) {
        this.service = service;
        this.settings = settings;
    }

    record Filters(@Size(max = 100) List<@NotBlank @Size(max = 128) String> documentIds) {}
    record SearchRequest(@NotBlank @Size(max = 2048) String query, @Min(1) @Max(20) Integer topK,
                         @Valid Filters filters, Mode mode, Boolean rerank) {}

    @PostMapping("/v1/search")
    SearchService.Result search(@Valid @RequestBody SearchRequest input) {
        if (!settings.evaluationEnabled() && (input.mode() != null || input.rerank() != null)) {
            throw new RagFailure(400, "Evaluation options require RAG_EVALUATION_ENABLED=true");
        }
        List<String> ids = input.filters() == null || input.filters().documentIds() == null
                ? List.of() : input.filters().documentIds();
        return service.search(input.query().strip(), input.topK() == null ? 5 : input.topK(), ids,
                input.mode() == null ? Mode.HYBRID : input.mode(), !Boolean.FALSE.equals(input.rerank()), UUID.randomUUID().toString());
    }

    @GetMapping("/health/live")
    Map<String, String> live() {
        return Map.of("status", "live");
    }

    @GetMapping("/health/ready")
    Map<String, String> ready() {
        return Map.of("status", "ready", "modelSignature", service.readySignature());
    }

    @ExceptionHandler(RagFailure.class)
    ResponseEntity<Map<String, String>> failure(RagFailure exception) {
        LOG.warn("status={} dependencyError={}", exception.status(), exception.getMessage());
        return ResponseEntity.status(exception.status()).body(Map.of("error", exception.getMessage()));
    }
}
