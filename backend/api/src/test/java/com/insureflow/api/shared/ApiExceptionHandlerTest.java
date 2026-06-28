package com.insureflow.api.shared;

import static org.hamcrest.Matchers.notNullValue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.insureflow.api.audit.AuditLoggingFilter;
import com.insureflow.api.security.JwtAuthenticationFilter;
import com.insureflow.api.shared.api.ApiExceptionHandler;
import com.insureflow.api.shared.error.BusinessRuleViolationException;
import com.insureflow.api.shared.error.ResourceNotFoundException;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@WebMvcTest(
        value = ApiExceptionHandlerTest.TestErrorController.class,
        excludeFilters =
                @ComponentScan.Filter(
                        type = org.springframework.context.annotation.FilterType.ASSIGNABLE_TYPE,
                        classes = {AuditLoggingFilter.class, JwtAuthenticationFilter.class}))
@AutoConfigureMockMvc(addFilters = false)
@Import({ApiExceptionHandler.class, ApiExceptionHandlerTest.TestErrorController.class})
class ApiExceptionHandlerTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void resourceNotFoundReturnsStructured404Response() throws Exception {
        mockMvc.perform(get("/test/not-found").accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.error").value("Not Found"))
                .andExpect(jsonPath("$.message").value("Policy POL-404 was not found"))
                .andExpect(jsonPath("$.path").value("/test/not-found"))
                .andExpect(jsonPath("$.timestamp", notNullValue()));
    }

    @Test
    void businessRuleViolationReturnsStructured422Response() throws Exception {
        mockMvc.perform(get("/test/business-rule").accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.status").value(422))
                .andExpect(jsonPath("$.error").value("Unprocessable Entity"))
                .andExpect(jsonPath("$.message").value("Only DRAFT policies can be activated"))
                .andExpect(jsonPath("$.path").value("/test/business-rule"))
                .andExpect(jsonPath("$.timestamp", notNullValue()));
    }

    @RestController
    static class TestErrorController {

        @GetMapping("/test/not-found")
        void notFound() {
            throw new ResourceNotFoundException("Policy POL-404 was not found");
        }

        @GetMapping("/test/business-rule")
        void businessRule() {
            throw new BusinessRuleViolationException("Only DRAFT policies can be activated");
        }
    }
}
