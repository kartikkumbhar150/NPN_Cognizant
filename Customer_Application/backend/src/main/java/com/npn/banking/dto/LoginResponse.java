package com.npn.banking.dto;

public class LoginResponse {
    private String token;
    private String customerId;
    private String firstName;
    private String lastName;
    private String email;
    private String customerSegmentType;

    public LoginResponse(String token, String customerId, String firstName,
                         String lastName, String email, String customerSegmentType) {
        this.token = token;
        this.customerId = customerId;
        this.firstName = firstName;
        this.lastName = lastName;
        this.email = email;
        this.customerSegmentType = customerSegmentType;
    }

    public String getToken() { return token; }
    public String getCustomerId() { return customerId; }
    public String getFirstName() { return firstName; }
    public String getLastName() { return lastName; }
    public String getEmail() { return email; }
    public String getCustomerSegmentType() { return customerSegmentType; }
}
