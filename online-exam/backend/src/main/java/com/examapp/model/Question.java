package com.examapp.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

@Entity
@Getter
@Setter
@Table(name = "questions")
public class Question {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @JsonProperty("questionText")
    @Column(name = "question_text")
    private String questionText;

    @JsonProperty("optionA")
    @Column(name = "option_a")
    private String optionA;

    @JsonProperty("optionB")
    @Column(name = "option_b")
    private String optionB;

    @JsonProperty("optionC")
    @Column(name = "option_c")
    private String optionC;

    @JsonProperty("optionD")
    @Column(name = "option_d")
    private String optionD;

    @JsonProperty("correctAnswer")
    @Column(name = "correct_answer")
    private String correctAnswer;
}

