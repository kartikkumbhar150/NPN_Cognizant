package com.npn.banking.controller;

import com.npn.banking.entity.Customer;
import com.npn.banking.repository.CustomerRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/customers")
public class CustomerController {

    private final CustomerRepository customerRepository;

    public CustomerController(CustomerRepository customerRepository) {
        this.customerRepository = customerRepository;
    }

    @GetMapping("/me")
    public ResponseEntity<?> getMe() {
        String customerId = (String) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return customerRepository.findByCustomerId(customerId)
                .map(c -> {
                    Map<String, Object> map = new java.util.LinkedHashMap<>();
                    map.put("customerId",          c.getCustomerId());
                    map.put("firstName",           c.getFirstName() != null ? c.getFirstName() : "");
                    map.put("lastName",            c.getLastName() != null ? c.getLastName() : "");
                    map.put("email",               c.getEmail() != null ? c.getEmail() : "");
                    map.put("mobileNumber",        c.getMobileNumber() != null ? c.getMobileNumber() : "");
                    map.put("age",                 c.getAge() != null ? c.getAge() : 0);
                    map.put("gender",              c.getGender() != null ? c.getGender() : "");
                    map.put("city",                c.getCity() != null ? c.getCity() : "");
                    map.put("state",               c.getState() != null ? c.getState() : "");
                    map.put("annualIncome",        c.getAnnualIncome() != null ? c.getAnnualIncome() : 0L);
                    map.put("creditScore",         c.getCreditScore() != null ? c.getCreditScore() : 0);
                    map.put("employmentType",      c.getEmploymentType() != null ? c.getEmploymentType() : "");
                    map.put("occupation",          c.getOccupation() != null ? c.getOccupation() : "");
                    map.put("customerSegmentType", c.getCustomerSegmentType() != null ? c.getCustomerSegmentType() : "");
                    map.put("customerSince",       c.getCustomerSince() != null ? c.getCustomerSince().toString() : "");
                    map.put("riskProfile",         c.getRiskProfile() != null ? c.getRiskProfile() : "");
                    return ResponseEntity.ok(map);
                })
                .orElseGet(() -> ResponseEntity.notFound().build());
    }
}
