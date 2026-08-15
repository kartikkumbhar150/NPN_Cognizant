package com.npn.banking.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@RestController
@RequestMapping("/api/ai")
public class AiController {

    @Value("${ai.engine.url}")
    private String aiEngineUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    /**
     * POST /api/ai/analyse
     * Proxies the request to the Python AI engine and returns the result.
     */
    @PostMapping("/analyse")
    public ResponseEntity<?> analyse() {
        String customerId = (String) SecurityContextHolder.getContext().getAuthentication().getPrincipal();

        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, String>> entity = new HttpEntity<>(
                    Map.of("customer_id", customerId), headers);

            ResponseEntity<Object> response = restTemplate.postForEntity(
                    aiEngineUrl + "/analyse", entity, Object.class);

            return ResponseEntity.status(response.getStatusCode()).body(response.getBody());

        } catch (Exception e) {
            return ResponseEntity.status(503).body(
                    Map.of("error", "AI engine unavailable: " + e.getMessage()));
        }
    }
}
