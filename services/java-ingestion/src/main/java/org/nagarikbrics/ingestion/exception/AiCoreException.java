package org.nagarikbrics.ingestion.exception;

/**
 * Exception thrown when communication with the Python AI Core service fails.
 *
 * <p>This can occur due to:</p>
 * <ul>
 *   <li>AI Core service being unreachable (network/container issue)</li>
 *   <li>AI Core returning a non-2xx HTTP status</li>
 *   <li>Request timeout (exceeding configured threshold)</li>
 *   <li>Response deserialization failure</li>
 * </ul>
 *
 * @author NagarikBRICS Team
 * @version 1.0.0-mvp
 */
public class AiCoreException extends RuntimeException {

    /**
     * Constructs an AiCoreException with a message.
     *
     * @param message description of the failure
     */
    public AiCoreException(final String message) {
        super(message);
    }

    /**
     * Constructs an AiCoreException with a message and root cause.
     *
     * @param message description of the failure
     * @param cause   the underlying exception
     */
    public AiCoreException(final String message, final Throwable cause) {
        super(message, cause);
    }
}
