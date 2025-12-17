package com.examapp.service;

import com.examapp.dto.ExamSubmissionRequest;
import com.examapp.model.Question;
import com.examapp.model.Result;
import com.examapp.model.User;
import com.examapp.model.UserAnswer;
import com.examapp.repository.QuestionRepository;
import com.examapp.repository.ResultRepository;
import com.examapp.repository.UserAnswerRepository;
import com.examapp.repository.UserRepository;

import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Service
public class ExamService {

    private final QuestionRepository questionRepo;
    private final UserAnswerRepository answerRepo;
    private final ResultRepository resultRepo;
    private final UserRepository userRepo;

    public ExamService(
            QuestionRepository questionRepo,
            UserAnswerRepository answerRepo,
            ResultRepository resultRepo,
            UserRepository userRepo) {
        this.questionRepo = questionRepo;
        this.answerRepo = answerRepo;
        this.resultRepo = resultRepo;
        this.userRepo = userRepo;
    }

    // ---------------------------------------------------------
    // SUBMIT EXAM — SINGLE ATTEMPT ENFORCED
    // ---------------------------------------------------------
    public String submitExam(ExamSubmissionRequest req) {

        // ❌ BLOCK MULTIPLE SUBMISSIONS
        Result prev = resultRepo.findTopByUserIdOrderBySubmittedAtDesc(req.getUserId());
        if (prev != null && prev.getSubmittedAt() != null) {
            return "You have already submitted the exam once. Multiple attempts are NOT allowed.";
        }

        // ⏱️ CHECK TIME LIMIT
        if (prev != null && prev.getEndTime() != null &&
                prev.getEndTime().isBefore(LocalDateTime.now())) {
            return "Time is over! Exam auto-submitted.";
        }

        double score = 0;

        User user = userRepo.findById(req.getUserId()).orElse(null);
        if (user == null) return "User not found";

        // Evaluate answers
        for (Long qid : req.getAnswers().keySet()) {

            String selected = req.getAnswers().get(qid);
            Question q = questionRepo.findById(qid).orElse(null);
            if (q == null) continue;

            boolean isCorrect = selected.equalsIgnoreCase(q.getCorrectAnswer());
            score += isCorrect ? 1 : -0.25;

            UserAnswer ua = new UserAnswer();
            ua.setUserId(req.getUserId());
            ua.setQuestionId(qid);
            ua.setSelectedOption(selected);
            ua.setCorrect(isCorrect);

            answerRepo.save(ua);
        }

        String status = score >= 30 ? "PASS" : "FAIL";

        Result result = new Result();
        result.setUserId(user.getId());
        result.setFullName(user.getFullName());
        result.setEmail(user.getEmail());
        result.setScore(score);
        result.setResultStatus(status);

        resultRepo.save(result);

        return "Exam submitted successfully!";
    }

    // ---------------------------------------------------------
    // GET RESULT (EMAIL + PASSWORD)
    // ---------------------------------------------------------
    public ResponseEntity<?> getUserResult(String email, String password) {

        User user = userRepo.findByEmail(email).orElse(null);
        if (user == null) {
            return ResponseEntity.badRequest().body(
                    Map.of("error", "Invalid email")
            );
        }

        if (!user.getPassword().equals(password)) {
            return ResponseEntity.badRequest().body(
                    Map.of("error", "Invalid password")
            );
        }

        Result result = resultRepo.findTopByUserIdOrderBySubmittedAtDesc(user.getId());
        if (result == null) {
            return ResponseEntity.badRequest().body(
                    Map.of("error", "No exam result found")
            );
        }

        Map<String, Object> response = new HashMap<>();
        response.put("name", user.getFullName());
        response.put("email", user.getEmail());
        response.put("score", result.getScore());
        response.put("status", result.getResultStatus());
        response.put("date", result.getSubmittedAt());

        return ResponseEntity.ok(response);
    }
}

