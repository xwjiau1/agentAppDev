package dev.agent.rag;

class RagFailure extends RuntimeException {
    private final int status;

    RagFailure(int status, String message) {
        this(status, message, null);
    }

    RagFailure(int status, String message, Throwable cause) {
        super(message, cause);
        this.status = status;
    }

    int status() {
        return status;
    }
}
