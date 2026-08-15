package com.npn.banking.repository;

import com.npn.banking.entity.Transaction;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TransactionRepository extends JpaRepository<Transaction, String> {

    Page<Transaction> findByCustomerIdOrderByTransactionDateDescTransactionTimeDesc(
            String customerId, Pageable pageable);

    List<Transaction> findByCustomerIdOrderByTransactionDateDesc(String customerId);

    @Query("""
            SELECT t.transactionType, t.merchantName, SUM(t.amount) as total
            FROM Transaction t
            WHERE t.customerId = :customerId AND t.transactionType = 'Debit'
            GROUP BY t.transactionType, t.merchantName
            ORDER BY total DESC
            """)
    List<Object[]> findSpendingByCategory(@Param("customerId") String customerId);
}
