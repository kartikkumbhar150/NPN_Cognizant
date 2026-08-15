package com.npn.banking.controller;

import com.npn.banking.entity.Transaction;
import com.npn.banking.repository.TransactionRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.*;

@RestController
@RequestMapping("/api/transactions")
public class TransactionController {

    private final TransactionRepository transactionRepository;

    public TransactionController(TransactionRepository transactionRepository) {
        this.transactionRepository = transactionRepository;
    }

    /** GET /api/transactions/me?page=0&size=20 */
    @GetMapping("/me")
    public ResponseEntity<?> getMyTransactions(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {

        String customerId = (String) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        Pageable pageable = PageRequest.of(page, size);
        Page<Transaction> txPage = transactionRepository
                .findByCustomerIdOrderByTransactionDateDescTransactionTimeDesc(customerId, pageable);

        List<Map<String, Object>> items = txPage.getContent().stream().map(this::txToMap).toList();

        return ResponseEntity.ok(Map.of(
                "content",       items,
                "totalElements", txPage.getTotalElements(),
                "totalPages",    txPage.getTotalPages(),
                "page",          page,
                "size",          size
        ));
    }

    /** GET /api/transactions/me/summary — category totals */
    @GetMapping("/me/summary")
    public ResponseEntity<?> getMySummary() {
        String customerId = (String) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        List<Transaction> all = transactionRepository.findByCustomerIdOrderByTransactionDateDesc(customerId);

        BigDecimal totalIncome  = BigDecimal.ZERO;
        BigDecimal totalSpend   = BigDecimal.ZERO;
        Map<String, BigDecimal> merchantTotals = new LinkedHashMap<>();
        Map<String, BigDecimal> monthlySpend   = new LinkedHashMap<>();

        for (Transaction tx : all) {
            if ("Credit".equalsIgnoreCase(tx.getTransactionType())) {
                totalIncome = totalIncome.add(tx.getAmount() != null ? tx.getAmount() : BigDecimal.ZERO);
            } else if ("Debit".equalsIgnoreCase(tx.getTransactionType())) {
                totalSpend = totalSpend.add(tx.getAmount() != null ? tx.getAmount() : BigDecimal.ZERO);

                String merchant = tx.getMerchantName() != null ? tx.getMerchantName() : "Other";
                merchantTotals.merge(merchant, tx.getAmount() != null ? tx.getAmount() : BigDecimal.ZERO, BigDecimal::add);

                if (tx.getTransactionDate() != null) {
                    String ym = tx.getTransactionDate().getYear() + "-" +
                                String.format("%02d", tx.getTransactionDate().getMonthValue());
                    monthlySpend.merge(ym, tx.getAmount() != null ? tx.getAmount() : BigDecimal.ZERO, BigDecimal::add);
                }
            }
        }

        // Top 8 merchants by spend
        List<Map<String, Object>> topMerchants = merchantTotals.entrySet().stream()
                .sorted(Map.Entry.<String, BigDecimal>comparingByValue().reversed())
                .limit(8)
                .map(e -> Map.<String, Object>of("name", e.getKey(), "amount", e.getValue()))
                .toList();

        // Monthly spend sorted chronologically
        List<Map<String, Object>> monthly = new ArrayList<>(monthlySpend.entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .map(e -> Map.<String, Object>of("month", e.getKey(), "amount", e.getValue()))
                .toList());

        return ResponseEntity.ok(Map.of(
                "totalIncome",  totalIncome,
                "totalSpend",   totalSpend,
                "savings",      totalIncome.subtract(totalSpend),
                "topMerchants", topMerchants,
                "monthlySpend", monthly,
                "txCount",      all.size()
        ));
    }

    private Map<String, Object> txToMap(Transaction tx) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("transactionId",          tx.getTransactionId());
        m.put("transactionDate",        tx.getTransactionDate() != null ? tx.getTransactionDate().toString() : null);
        m.put("transactionType",        tx.getTransactionType());
        m.put("transactionMode",        tx.getTransactionMode());
        m.put("amount",                 tx.getAmount());
        m.put("currency",               tx.getCurrency());
        m.put("merchantName",           tx.getMerchantName());
        m.put("transactionDescription", tx.getTransactionDescription());
        m.put("transactionStatus",      tx.getTransactionStatus());
        m.put("channel",                tx.getChannel());
        m.put("locationCity",           tx.getLocationCity());
        return m;
    }
}
