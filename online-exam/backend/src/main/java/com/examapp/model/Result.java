package com.examapp.model;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import java.time.LocalDateTime;

@Getter
@Setter
@Entity
@Table(name = "results")
public class Result {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long userId;
    private String fullName;
    private String email;

    private double score;
    private String resultStatus;

    private LocalDateTime submittedAt = LocalDateTime.now();

    // NEW FIELDS FOR TIMER
    private LocalDateTime startTime;
    private LocalDateTime endTime;
}

