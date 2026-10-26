package com.insureflow.api.security;

import java.util.Set;

public record JwtPrincipal(String subject, Set<InsureFlowRole> roles) {}
