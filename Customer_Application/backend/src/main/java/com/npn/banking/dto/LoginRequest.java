package com.npn.banking.dto;

public class LoginRequest {
    private String customerId;
    private String password;

    public String getCustomerId() { return customerId; }
    public void setCustomerId(String customerId) { this.customerId = customerId; }

    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }
}
