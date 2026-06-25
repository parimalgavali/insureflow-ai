package com.insureflow.api.policy.service;

import com.insureflow.api.policy.api.dto.AddCoverageRequest;
import com.insureflow.api.policy.api.dto.CoverageResponse;
import com.insureflow.api.policy.api.dto.CreateCustomerRequest;
import com.insureflow.api.policy.api.dto.CreatePolicyRequest;
import com.insureflow.api.policy.api.dto.CustomerResponse;
import com.insureflow.api.policy.api.dto.PolicyResponse;
import com.insureflow.api.policy.domain.Coverage;
import com.insureflow.api.policy.domain.Customer;
import com.insureflow.api.policy.domain.Policy;
import com.insureflow.api.policy.domain.PolicyStatus;
import com.insureflow.api.policy.repository.CoverageRepository;
import com.insureflow.api.policy.repository.CustomerRepository;
import com.insureflow.api.policy.repository.PolicyRepository;
import com.insureflow.api.shared.error.ResourceNotFoundException;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PolicyManagementService {

    private final CustomerRepository customerRepository;
    private final PolicyRepository policyRepository;
    private final CoverageRepository coverageRepository;

    public PolicyManagementService(
            CustomerRepository customerRepository,
            PolicyRepository policyRepository,
            CoverageRepository coverageRepository) {
        this.customerRepository = customerRepository;
        this.policyRepository = policyRepository;
        this.coverageRepository = coverageRepository;
    }

    @Transactional
    public CustomerResponse createCustomer(CreateCustomerRequest request) {
        Customer customer = new Customer();
        customer.setCustomerNumber(request.customerNumber());
        customer.setFirstName(request.firstName());
        customer.setLastName(request.lastName());
        customer.setEmail(request.email());
        customer.setPhone(request.phone());
        customer.setAddressLine1(request.addressLine1());
        customer.setAddressLine2(request.addressLine2());
        customer.setCity(request.city());
        customer.setState(request.state());
        customer.setPostalCode(request.postalCode());
        customer.setCountry(request.country());
        return CustomerResponse.from(customerRepository.save(customer));
    }

    @Transactional(readOnly = true)
    public CustomerResponse getCustomer(String customerNumber) {
        return CustomerResponse.from(findCustomer(customerNumber));
    }

    @Transactional
    public PolicyResponse createPolicy(CreatePolicyRequest request) {
        validateDates(request.effectiveDate(), request.expirationDate());
        Customer customer = findCustomer(request.customerNumber());

        Policy policy = new Policy();
        policy.setCustomer(customer);
        policy.setPolicyNumber(request.policyNumber());
        policy.setPolicyType(request.policyType());
        policy.setStatus(PolicyStatus.DRAFT);
        policy.setEffectiveDate(request.effectiveDate());
        policy.setExpirationDate(request.expirationDate());
        policy.setPremiumAmount(request.premiumAmount());
        policy.setCurrency(request.currency());

        return PolicyResponse.from(policyRepository.save(policy), List.of());
    }

    @Transactional(readOnly = true)
    public PolicyResponse getPolicy(String policyNumber) {
        Policy policy = findPolicy(policyNumber);
        return PolicyResponse.from(policy, coverageRepository.findByPolicyPolicyNumber(policyNumber));
    }

    @Transactional
    public CoverageResponse addCoverage(String policyNumber, AddCoverageRequest request) {
        validateDates(request.effectiveDate(), request.expirationDate());
        Policy policy = findPolicy(policyNumber);

        Coverage coverage = new Coverage();
        coverage.setPolicy(policy);
        coverage.setCoverageCode(request.coverageCode());
        coverage.setCoverageName(request.coverageName());
        coverage.setCoverageType(request.coverageType());
        coverage.setLimitAmount(request.limitAmount());
        coverage.setDeductibleAmount(request.deductibleAmount());
        coverage.setEffectiveDate(request.effectiveDate());
        coverage.setExpirationDate(request.expirationDate());
        coverage.setExclusions(request.exclusions());
        return CoverageResponse.from(coverageRepository.save(coverage));
    }

    private Customer findCustomer(String customerNumber) {
        return customerRepository
                .findByCustomerNumber(customerNumber)
                .orElseThrow(() -> new ResourceNotFoundException("Customer " + customerNumber + " was not found"));
    }

    private Policy findPolicy(String policyNumber) {
        return policyRepository
                .findByPolicyNumber(policyNumber)
                .orElseThrow(() -> new ResourceNotFoundException("Policy " + policyNumber + " was not found"));
    }

    private void validateDates(java.time.LocalDate effectiveDate, java.time.LocalDate expirationDate) {
        if (!effectiveDate.isBefore(expirationDate)) {
            throw new IllegalArgumentException("effectiveDate must be before expirationDate");
        }
    }
}
