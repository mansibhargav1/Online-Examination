package com.examapp.controller;

import com.examapp.model.Question;
import com.examapp.repository.QuestionRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/questions")
@CrossOrigin(origins = "*")
public class QuestionController {

    @Autowired
    private QuestionRepository questionRepo;

    // Get all questions
    @GetMapping("/all")
    public ResponseEntity<?> getAllQuestions() {
        return ResponseEntity.ok(questionRepo.findAll());
    }

    // ⭐ NEW — Add Question API
    @PostMapping("/add")
    public ResponseEntity<?> addQuestion(@RequestBody Question question) {
        try {
            questionRepo.save(question);
            return ResponseEntity.ok("Question added successfully!");
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Failed to add question: " + e.getMessage());
        }
    }
    // UPDATE question
    @PutMapping("/update/{id}")
    public ResponseEntity<?> updateQuestion(@PathVariable Long id, @RequestBody Question q) {
        return questionRepo.findById(id)
            .map(existing -> {
                existing.setQuestionText(q.getQuestionText());
                existing.setOptionA(q.getOptionA());
                existing.setOptionB(q.getOptionB());
                existing.setOptionC(q.getOptionC());
                existing.setOptionD(q.getOptionD());
                existing.setCorrectAnswer(q.getCorrectAnswer());
                questionRepo.save(existing);
                return ResponseEntity.ok("Question updated successfully!");
            })
            .orElse(ResponseEntity.badRequest().body("Question not found"));
    }
    @DeleteMapping("/delete/{id}")
    public ResponseEntity<?> deleteQuestion(@PathVariable Long id) {
        if (!questionRepo.existsById(id)) {
            return ResponseEntity.badRequest().body("Question not found");
        }
    
        questionRepo.deleteById(id);
        return ResponseEntity.ok("Question deleted successfully!");
    }
    
}

