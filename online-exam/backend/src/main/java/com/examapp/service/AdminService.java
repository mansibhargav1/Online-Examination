package com.examapp.service;

import com.examapp.model.Admin;
import com.examapp.repository.AdminRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class AdminService {

    @Autowired
    private AdminRepository adminRepo;

    // Admin Signup
    public String signup(String fullName, String email, String password) {

        // Check if admin already exists
        Admin existing = adminRepo.findByEmail(email);
        if (existing != null) {
            return "Admin already exists!";
        }

        // Create new admin
        Admin admin = new Admin();
        admin.setFullName(fullName);
        admin.setEmail(email);
        admin.setPassword(password);

        // Save to DB
        adminRepo.save(admin);

        return "success";
    }

    // Admin Login
    public String login(String email, String password) {

        Admin admin = adminRepo.findByEmail(email);

        if (admin == null) {
            return "Admin not found!";
        }

        if (!admin.getPassword().equals(password)) {
            return "Incorrect password!";
        }

        return "success";
    }
}

