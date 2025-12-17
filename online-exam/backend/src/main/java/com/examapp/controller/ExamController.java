package com.examapp.controller;

import com.examapp.dto.ExamSubmissionRequest;
import com.examapp.model.Result;
import com.examapp.repository.ResultRepository;
import com.examapp.service.ExamService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.Map;

@RestController
@RequestMapping("/api/exam")
@CrossOrigin(origins = "*")
public class ExamController {

    private final ExamService examService;
    private final ResultRepository resultRepo;

    public ExamController(ExamService examService, ResultRepository resultRepo) {
        this.examService = examService;
        this.resultRepo = resultRepo;
    }

    // ------------------------------------------------------
    // START EXAM — ALLOW ONLY ONCE
    // ------------------------------------------------------
    @GetMapping("/start")
    public ResponseEntity<?> startExam(@RequestParam Long userId) {

        // ❌ BLOCK IF USER ALREADY SUBMITTED
        Result previous = resultRepo.findTopByUserIdOrderBySubmittedAtDesc(userId);
        if (previous != null && previous.getSubmittedAt() != null) {
            return ResponseEntity.badRequest().body(
                Map.of("error", "You have already completed the exam. Only one attempt allowed.")
            );
        }

        LocalDateTime now = LocalDateTime.now();
        LocalDateTime end = now.plusMinutes(60);

        Result temp = new Result();
        temp.setUserId(userId);
        temp.setStartTime(now);
        temp.setEndTime(end);
        resultRepo.save(temp);

        return ResponseEntity.ok(Map.of(
                "startTime", now.toString(),
                "endTime", end.toString(),
                "remainingSeconds", 3600
        ));
    }

    // ------------------------------------------------------
    // SUBMIT EXAM
    // ------------------------------------------------------
    @PostMapping("/submit")
    public String submitExam(@RequestBody ExamSubmissionRequest req) {
        return examService.submitExam(req);
    }

    // ------------------------------------------------------
    // GET RESULT
    // ------------------------------------------------------
    @GetMapping("/result")
    public ResponseEntity<?> getUserResult(
            @RequestParam String email,
            @RequestParam String password) {

        return examService.getUserResult(email, password);
    }
}

