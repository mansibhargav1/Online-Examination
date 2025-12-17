package com.examapp.repository;

import com.examapp.model.Result;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ResultRepository extends JpaRepository<Result, Long> {

    // Fetch latest exam result for a user
    Result findTopByUserIdOrderBySubmittedAtDesc(Long userId);
}

