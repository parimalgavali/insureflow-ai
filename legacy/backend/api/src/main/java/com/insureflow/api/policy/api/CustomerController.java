package com.insureflow.api.policy.api;

import com.insureflow.api.policy.api.dto.CreateCustomerRequest;
import com.insureflow.api.policy.api.dto.CustomerResponse;
import com.insureflow.api.policy.service.PolicyManagementService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/customers")
class CustomerController {

    private final PolicyManagementService service;

    CustomerController(PolicyManagementService service) {
        this.service = service;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    CustomerResponse createCustomer(@Valid @RequestBody CreateCustomerRequest request) {
        return service.createCustomer(request);
    }

    @GetMapping("/{customerNumber}")
    CustomerResponse getCustomer(@PathVariable String customerNumber) {
        return service.getCustomer(customerNumber);
    }
}
