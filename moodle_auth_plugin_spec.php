<?php
/**
 * Inovatx SSO Authentication Plugin for Moodle
 * 
 * Task 3.3.2: Build Moodle authentication plugin integration
 * 
 * This plugin validates signed JWTs issued by Django Core (Task 3.3.1)
 * and creates Moodle sessions, redirecting users to their designated
 * course interface at learn.inovatx.com.
 * 
 * Plugin location: moodle/local/inovatx_sso/auth.php
 * Version: 1.0
 * Requires: Moodle 4.x
 * Requires: Django Core JWT secret key (shared via JWT_SECRET_KEY env)
 */

defined('MOODLE_INTERNAL') || die();

require_once($CFG->libdir . '/authlib.php');
require_once($CFG->dirroot . '/lib/weblib.php');

class auth_inovatx_sso extends plugin_auth {
    
    /**
     * Plugin name.
     * @var string
     */
    public $name = 'inovatx_sso';
    
    /**
     * Whether this plugin allows users to change their password.
     * @var bool
     */
    public $changepassword = false;
    
    /**
     * Whether this plugin allows users to reset their password.
     * @var bool
     */
    public $resetpassword = false;
    
    /**
     * Whether this plugin allows manual user creation.
     * @var bool
     */
    public $manualuser = false;
    
    /**
     * Django Core JWT configuration (shared secret with Django).
     * These should be set in Moodle config.php or via admin settings.
     */
    const JWT_ISSUER = 'inovatax-django-core';
    const JWT_AUDIENCE = 'inovatax-moodle-lms';
    const JWT_ALGORITHM = 'HS256';
    
    /**
     * Authenticate user via JWT issued by Django Core.
     * 
     * @param string $username
     * @param string $password
     * @return bool
     */
    public function user_login($username, $password) {
        global $CFG, $SESSION, $USER;
        
        // JWT is passed as the 'password' parameter from Django redirect
        $jwt = $password;
        
        if (empty($jwt)) {
            return false;
        }
        
        // Validate JWT signature and claims
        $payload = $this->validate_jwt($jwt);
        if ($payload === false) {
            return false;
        }
        
        // Extract user identity from JWT claims
        $user_id = $payload['user_id'] ?? null;
        $organization_id = $payload['organization_id'] ?? null;
        $cohort_ids = $payload['cohort_ids'] ?? [];
        $roles = $payload['roles'] ?? [];
        
        if (empty($user_id) || empty($organization_id)) {
            return false;
        }
        
        // Find or create Moodle user account
        $moodle_user = $this->find_or_create_user($payload);
        if ($moodle_user === false) {
            return false;
        }
        
        // Assign user to appropriate Moodle cohort based on JWT cohort_ids
        $this->assign_cohorts($moodle_user, $cohort_ids);
        
        // Create Moodle session
        $SESSION->wantsurl = moodle_url('/course/index.php')->out();
        complete_user_login($moodle_user);
        
        return true;
    }
    
    /**
     * Validate JWT signature and claims.
     * 
     * @param string $jwt
     * @return array|false
     */
    private function validate_jwt($jwt) {
        global $CFG;
        
        $secret_key = get_config('local_inovatx_sso', 'jwt_secret_key');
        if (empty($secret_key)) {
            $secret_key = $CFG->passwordsaltmain; // Fallback to Moodle password salt
        }
        
        try {
            // Use a JWT library (e.g., firebase/php-jwt or lcobucci/jwt)
            $decoded = \Firebase\JWT\JWT::decode(
                $jwt,
                $secret_key,
                [self::JWT_ALGORITHM]
            );
            
            $payload = (array) $decoded;
            
            // Validate issuer
            if (!isset($payload['iss']) || $payload['iss'] !== self::JWT_ISSUER) {
                return false;
            }
            
            // Validate audience
            if (!isset($payload['aud']) || $payload['aud'] !== self::JWT_AUDIENCE) {
                return false;
            }
            
            // Validate expiration
            if (!isset($payload['exp']) || $payload['exp'] < time()) {
                return false;
            }
            
            // Validate issued at
            if (!isset($payload['iat'])) {
                return false;
            }
            
            return $payload;
            
        } catch (\Exception $e) {
            return false;
        }
    }
    
    /**
     * Find existing Moodle user or create new one from JWT payload.
     * 
     * @param array $payload
     * @return stdClass|false
     */
    private function find_or_create_user($payload) {
        global $DB;
        
        $username = $payload['user_id'] ?? null;
        $firstname = $payload['firstname'] ?? '';
        $lastname = $payload['lastname'] ?? '';
        $email = $payload['email'] ?? '';
        
        if (empty($username)) {
            return false;
        }
        
        // Try to find existing user by username
        $user = $DB->get_record('user', ['username' => $username]);
        
        if ($user) {
            // Update user details if needed
            if ($user->firstname !== $firstname || $user->lastname !== $lastname || $user->email !== $email) {
                $user->firstname = $firstname;
                $user->lastname = $lastname;
                $user->email = $email;
                $DB->update_record('user', $user);
            }
            return $user;
        }
        
        // Create new Moodle user
        $newuser = new stdClass();
        $newuser->username = $username;
        $newuser->firstname = $firstname;
        $newuser->lastname = $lastname;
        $newuser->email = $email;
        $newuser->auth = 'inovatx_sso';
        $newuser->confirmed = 1;
        $newuser->policyaccepted = 1;
        $newuser->timecreated = time();
        $newuser->idnumber = $payload['organization_id'] ?? '';
        
        $userid = $DB->insert_record('user', $newuser, true);
        $newuser->id = $userid;
        
        return $newuser;
    }
    
    /**
     * Assign user to Moodle cohorts based on JWT cohort_ids.
     * 
     * @param stdClass $user
     * @param array $cohort_ids
     * @return void
     */
    private function assign_cohorts($user, $cohort_ids) {
        global $DB;
        
        if (empty($cohort_ids)) {
            return;
        }
        
        foreach ($cohort_ids as $cohort_id) {
            // Check if cohort exists
            $cohort = $DB->get_record('cohort', ['id' => $cohort_id]);
            if (!$cohort) {
                continue;
            }
            
            // Check if already a member
            $existing = $DB->get_record('cohort_members', [
                'cohortid' => $cohort_id,
                'userid' => $user->id
            ]);
            
            if (!$existing) {
                $member = new stdClass();
                $member->cohortid = $cohort_id;
                $member->userid = $user->id;
                $member->timeadded = time();
                $DB->insert_record('cohort_members', $member);
            }
        }
    }
    
    /**
     * Return login URL for SSO initiation.
     * 
     * @return string
     */
    public function loginurl() {
        // Redirect to Django Core SSO token issuance endpoint
        $djangosso_url = get_config('local_inovatx_sso', 'django_sso_url');
        if (empty($djangosso_url)) {
            return new moodle_url('/login/index.php');
        }
        
        return new moodle_url($djangosso_url);
    }
    
    /**
     * Whether this plugin is available for use.
     * 
     * @return bool
     */
    public function is_available() {
        return true;
    }
    
    /**
     * Whether this plugin can change user data.
     * 
     * @return bool
     */
    public function can_change_userdata() {
        return false;
    }
    
    /**
     * Whether this plugin can change password.
     * 
     * @return bool
     */
    public function can_change_password() {
        return false;
    }
    
    /**
     * Whether this plugin can reset password.
     * 
     * @return bool
     */
    public function can_reset_password() {
        return false;
    }
    
    /**
     * Get user fields available for editing.
     * 
     * @return array
     */
    public function is_field_editable($field) {
        return false;
    }
}
