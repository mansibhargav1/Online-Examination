package com.examapp.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.examapp.model.User;
import com.examapp.repository.UserRepository;

@Service
public class AuthService {

    @Autowired
    private UserRepository userRepository;

    public String signup(String fullName, String email, String password) {
        if (userRepository.existsByEmail(email)) {
            return "Email already exists";
        }

        User user = new User();
        user.setFullName(fullName);
        user.setEmail(email);
        user.setPassword(password);

        userRepository.save(user);
        return "success";
    }

    // 🔥 RETURN USER ID INSTEAD OF "success"
    public String login(String email, String password) {

        return userRepository.findByEmail(email)
                .map(user ->
                        user.getPassword().equals(password)
                                ? String.valueOf(user.getId()) // return USER ID
                                : "Invalid password"
                )
                .orElse("Invalid email");
    }
}

