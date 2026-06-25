package com.insureflow.api.policy.api.dto;

import com.insureflow.api.policy.domain.Customer;

public record CustomerResponse(
        String customerNumber,
        String firstName,
        String lastName,
        String email,
        String phone,
        String addressLine1,
        String addressLine2,
        String city,
        String state,
        String postalCode,
        String country) {

    public static CustomerResponse from(Customer customer) {
        return new CustomerResponse(
                customer.getCustomerNumber(),
                customer.getFirstName(),
                customer.getLastName(),
                customer.getEmail(),
                customer.getPhone(),
                customer.getAddressLine1(),
                customer.getAddressLine2(),
                customer.getCity(),
                customer.getState(),
                customer.getPostalCode(),
                customer.getCountry());
    }
}
