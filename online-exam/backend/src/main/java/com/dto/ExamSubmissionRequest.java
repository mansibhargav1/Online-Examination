package com.examapp.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.Map;

@Getter
@Setter
public class ExamSubmissionRequest {
    private Long userId;   // the logged-in user ID
    private Map<Long, String> answers;  // questionId -> selectedOption
}

