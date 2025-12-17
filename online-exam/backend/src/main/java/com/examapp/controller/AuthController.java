package com.examapp.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import com.examapp.service.AuthService;

@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = "*")
public class AuthController {

    @Autowired
    private AuthService authService;

    @PostMapping("/signup")
    public ResponseEntity<String> signup(@RequestBody SignupRequest req) {
        String result = authService.signup(req.getFullName(), req.getEmail(), req.getPassword());

        return result.equals("success")
                ? ResponseEntity.ok("success")
                : ResponseEntity.badRequest().body(result);
    }

    // 🔥 THIS NOW RETURNS USER ID
    @PostMapping("/login")
    public ResponseEntity<String> login(@RequestBody LoginRequest req) {
        String result = authService.login(req.getEmail(), req.getPassword());

        // If result is numeric → it's userId
        if (result.matches("\\d+")) {
            return ResponseEntity.ok(result);
        }

        return ResponseEntity.badRequest().body(result);
    }
}

