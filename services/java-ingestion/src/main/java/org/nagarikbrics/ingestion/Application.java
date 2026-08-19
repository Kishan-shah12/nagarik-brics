package org.nagarikbrics.ingestion;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Entry point for the NagarikBRICS Java Ingestion Microservice.
 *
 * <p>This service is the data gateway for citizen feedback. It accepts
 * multilingual feedback submissions via REST API, validates them against
 * strict schema contracts, and forwards them to the Python AI Core for
 * NLP processing (translation, classification, sentiment analysis).</p>
 *
 * <h2>Responsibilities</h2>
 * <ul>
 *   <li>Accept {@code POST /api/v1/feedback/submit} requests</li>
 *   <li>Validate payloads against {@code CitizenFeedbackRequest} schema</li>
 *   <li>Forward validated feedback to Python AI Core via HTTP</li>
 *   <li>Return enriched {@code CitizenFeedbackRecord} to the caller</li>
 * </ul>
 *
 * @author NagarikBRICS Team
 * @version 1.0.0-mvp
 * @see <a href="../../api-docs.md">API Contract Specification</a>
 */
@SpringBootApplication
public class Application {

    /**
     * Bootstrap the Spring Boot application.
     *
     * @param args command-line arguments (none expected for standard operation)
     */
    public static void main(final String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
