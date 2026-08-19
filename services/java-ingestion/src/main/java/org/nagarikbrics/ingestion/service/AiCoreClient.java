package org.nagarikbrics.ingestion.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.nagarikbrics.ingestion.exception.AiCoreException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Map;

/**
 * HTTP client for communicating with the Python AI Core microservice.
 *
 * <p>Sends validated citizen feedback to the AI Core's internal processing
 * endpoint ({@code POST /internal/process}) and returns the NLP-enriched
 * response. This endpoint is internal to the Docker bridge network and
 * is NOT exposed publicly.</p>
 *
 * <h2>Communication Flow</h2>
 * <pre>
 * Java Ingestion ──(HTTP POST)──▶ Python AI Core /internal/process
 *                 ◀──(JSON)────── { translated_text, sentiment, category, ... }
 * </pre>
 *
 * <h2>Error Handling</h2>
 * <ul>
 *   <li>Connection timeout → {@link AiCoreException}</li>
 *   <li>Non-2xx response → {@link AiCoreException} with status code</li>
 *   <li>JSON parse failure → {@link AiCoreException}</li>
 * </ul>
 *
 * @author NagarikBRICS Team
 * @version 1.0.0-mvp
 */
@Service
public class AiCoreClient {

    private static final Logger LOG = LoggerFactory.getLogger(AiCoreClient.class);

    /** The base URL of the Python AI Core service. */
    private final String baseUrl;

    /** The internal processing endpoint path. */
    private final String processEndpoint;

    /** HTTP request timeout in milliseconds. */
    private final int timeoutMs;

    /** Jackson ObjectMapper for JSON serialization/deserialization. */
    private final ObjectMapper objectMapper;

    /** Reusable HTTP client (thread-safe, connection-pooling). */
    private final HttpClient httpClient;

    /**
     * Constructs the AI Core client with configuration from application.yml.
     *
     * @param baseUrl         the base URL (e.g., "http://python-ai-core:8080")
     * @param processEndpoint the process endpoint path (e.g., "/internal/process")
     * @param timeoutMs       request timeout in milliseconds
     * @param objectMapper    Spring-managed Jackson ObjectMapper
     */
    public AiCoreClient(
            @Value("${app.ai-core.base-url}") final String baseUrl,
            @Value("${app.ai-core.process-endpoint}") final String processEndpoint,
            @Value("${app.ai-core.timeout-ms}") final int timeoutMs,
            final ObjectMapper objectMapper) {
        this.baseUrl = baseUrl;
        this.processEndpoint = processEndpoint;
        this.timeoutMs = timeoutMs;
        this.objectMapper = objectMapper;
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofMillis(timeoutMs))
                .build();
    }

    /**
     * Sends validated feedback to the AI Core for NLP processing.
     *
     * <p>Constructs the internal process request payload, sends it to the
     * AI Core, and parses the enriched response. The AI Core performs
     * translation, sentiment analysis, category classification, and
     * urgency scoring via Gemini.</p>
     *
     * @param feedbackId  the UUID assigned to this feedback record
     * @param rawText     the original feedback text
     * @param language    the ISO 639-1 language code
     * @param lat         latitude of the issue location
     * @param lng         longitude of the issue location
     * @param countryCode the BRICS country code (may be null)
     * @return parsed JSON response from AI Core as a JsonNode tree
     * @throws AiCoreException if the AI Core is unreachable, returns an error,
     *                         or the response cannot be parsed
     */
    public JsonNode processFeedback(final String feedbackId,
                                     final String rawText,
                                     final String language,
                                     final double lat,
                                     final double lng,
                                     final String countryCode) {
        try {
            // Build the internal process request payload
            final Map<String, Object> payload = Map.of(
                    "feedback_id", feedbackId,
                    "raw_text", rawText,
                    "language", language,
                    "location_coords", Map.of("lat", lat, "lng", lng),
                    "country_code", countryCode != null ? countryCode : ""
            );

            final String requestBody = objectMapper.writeValueAsString(payload);
            final String url = baseUrl + processEndpoint;

            LOG.info("Sending feedback {} to AI Core: {}", feedbackId, url);

            final HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofMillis(timeoutMs))
                    .POST(HttpRequest.BodyPublishers.ofString(requestBody))
                    .build();

            final HttpResponse<String> response = httpClient.send(
                    request, HttpResponse.BodyHandlers.ofString()
            );

            if (response.statusCode() < 200 || response.statusCode() >= 300) {
                throw new AiCoreException(String.format(
                        "AI Core returned HTTP %d for feedback %s: %s",
                        response.statusCode(), feedbackId, response.body()
                ));
            }

            LOG.info("AI Core processed feedback {} successfully (HTTP {})",
                    feedbackId, response.statusCode());

            return objectMapper.readTree(response.body());

        } catch (final AiCoreException ex) {
            throw ex; // Re-throw our own exceptions as-is
        } catch (final Exception ex) {
            throw new AiCoreException(
                    "Failed to communicate with AI Core for feedback " + feedbackId, ex
            );
        }
    }
}
