package com.examapp.service;

import com.examapp.model.Question;
import com.examapp.repository.QuestionRepository;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class QuestionService {

    private final QuestionRepository repo;

    public QuestionService(QuestionRepository repo) {
        this.repo = repo;
    }

    public List<Question> getAllQuestions() {
        return repo.findAll();
    }
}

