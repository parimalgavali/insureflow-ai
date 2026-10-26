package com.insureflow.api.security;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import java.util.Set;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/auth")
class AuthController {

    private final JwtService jwtService;

    AuthController(JwtService jwtService) {
        this.jwtService = jwtService;
    }

    @PostMapping("/dev-token")
    TokenResponse createDevToken(@Valid @RequestBody TokenRequest request) {
        return new TokenResponse(jwtService.createToken(request.subject(), request.roles()));
    }

    record TokenRequest(@NotBlank String subject, @NotEmpty Set<InsureFlowRole> roles) {}

    record TokenResponse(String token) {}
}
