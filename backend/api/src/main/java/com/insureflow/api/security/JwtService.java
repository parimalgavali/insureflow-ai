package com.insureflow.api.security;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Instant;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class JwtService {

    private static final Base64.Encoder URL_ENCODER = Base64.getUrlEncoder().withoutPadding();
    private static final Base64.Decoder URL_DECODER = Base64.getUrlDecoder();

    private final JwtProperties properties;
    private final ObjectMapper objectMapper;
    private final Clock clock;

    @Autowired
    public JwtService(JwtProperties properties, ObjectMapper objectMapper) {
        this(properties, objectMapper, Clock.systemUTC());
    }

    JwtService(JwtProperties properties, ObjectMapper objectMapper, Clock clock) {
        this.properties = properties;
        this.objectMapper = objectMapper;
        this.clock = clock;
    }

    public String createToken(String subject, Set<InsureFlowRole> roles) {
        Instant now = Instant.now(clock);
        Map<String, Object> header = Map.of("alg", "HS256", "typ", "JWT");
        Map<String, Object> payload = Map.of(
                "iss", properties.issuer(),
                "sub", subject,
                "roles", roles.stream().map(Enum::name).sorted().toList(),
                "iat", now.getEpochSecond(),
                "exp", now.plusSeconds(properties.expiresInMinutes() * 60).getEpochSecond());
        String encodedHeader = encode(header);
        String encodedPayload = encode(payload);
        String signingInput = encodedHeader + "." + encodedPayload;
        return signingInput + "." + sign(signingInput);
    }

    public JwtPrincipal validate(String token) {
        String[] parts = token.split("\\.");
        if (parts.length != 3) {
            throw new IllegalArgumentException("Invalid JWT format");
        }
        String signingInput = parts[0] + "." + parts[1];
        if (!sign(signingInput).equals(parts[2])) {
            throw new IllegalArgumentException("Invalid JWT signature");
        }
        Map<String, Object> payload = decode(parts[1]);
        if (!properties.issuer().equals(payload.get("iss"))) {
            throw new IllegalArgumentException("Invalid JWT issuer");
        }
        Number exp = (Number) payload.get("exp");
        if (exp == null || Instant.now(clock).getEpochSecond() >= exp.longValue()) {
            throw new IllegalArgumentException("JWT is expired");
        }
        String subject = (String) payload.get("sub");
        Object rolesClaim = payload.getOrDefault("roles", List.of());
        List<String> roleNames = rolesClaim instanceof List<?> values
                ? values.stream().map(String::valueOf).toList()
                : List.of();
        Set<InsureFlowRole> roles = roleNames.stream()
                .map(InsureFlowRole::valueOf)
                .collect(Collectors.toUnmodifiableSet());
        return new JwtPrincipal(subject, roles);
    }

    private String encode(Map<String, Object> value) {
        try {
            return URL_ENCODER.encodeToString(objectMapper.writeValueAsBytes(value));
        } catch (Exception exception) {
            throw new IllegalStateException("Unable to encode JWT", exception);
        }
    }

    private Map<String, Object> decode(String value) {
        try {
            return objectMapper.readValue(URL_DECODER.decode(value), new TypeReference<>() {});
        } catch (Exception exception) {
            throw new IllegalArgumentException("Unable to decode JWT", exception);
        }
    }

    private String sign(String signingInput) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(properties.secret().getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            return URL_ENCODER.encodeToString(mac.doFinal(signingInput.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception exception) {
            throw new IllegalStateException("Unable to sign JWT", exception);
        }
    }
}
