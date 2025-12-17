package com.examapp.controller;

import com.examapp.service.AdminService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/admin")
@CrossOrigin(origins = "*")
public class AdminController {

    @Autowired
    private AdminService adminService;

    @PostMapping("/signup")
    public String signup(@RequestBody AdminSignupRequest req) {
        return adminService.signup(req.fullName, req.email, req.password);
    }

    @PostMapping("/login")
    public String login(@RequestBody AdminLoginRequest req) {
        return adminService.login(req.email, req.password);
    }
}

