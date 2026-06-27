package com.insureflow.api.security;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "insureflow.security.jwt")
public record JwtProperties(String issuer, String secret, long expiresInMinutes) {}
