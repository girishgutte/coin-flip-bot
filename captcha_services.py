import requests
import json
import logging
from typing import Optional, Dict, Any
import time
import base64

logger = logging.getLogger(__name__)


class CaptchaService:
    """Base class for captcha solving services"""
    
    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
    
    def solve(self, captcha_data: Dict[str, Any]) -> Optional[str]:
        """Solve captcha and return solution. Must be implemented by subclass"""
        raise NotImplementedError


class CapSolverService(CaptchaService):
    """CapSolver API integration"""
    
    BASE_URL = "https://api.capsolver.com"
    
    def solve(self, captcha_data: Dict[str, Any]) -> Optional[str]:
        """
        Solve captcha using CapSolver
        captcha_data should contain: type, websiteURL, websiteKey
        """
        try:
            # Create task
            create_url = f"{self.BASE_URL}/createTask"
            payload = {
                "clientKey": self.api_key,
                "task": captcha_data
            }
            
            response = requests.post(create_url, json=payload, timeout=self.timeout)
            result = response.json()
            
            if result.get("errorId") != 0:
                logger.error(f"CapSolver create task error: {result}")
                return None
            
            task_id = result.get("taskId")
            logger.info(f"CapSolver task created: {task_id}")
            
            # Poll for result
            return self._get_result(task_id)
        
        except Exception as e:
            logger.error(f"CapSolver error: {e}")
            return None
    
    def _get_result(self, task_id: int, max_attempts: int = 60) -> Optional[str]:
        """Poll CapSolver for result"""
        get_url = f"{self.BASE_URL}/getTaskResult"
        
        for attempt in range(max_attempts):
            try:
                payload = {
                    "clientKey": self.api_key,
                    "taskId": task_id
                }
                
                response = requests.post(get_url, json=payload, timeout=self.timeout)
                result = response.json()
                
                if result.get("status") == "ready":
                    solution = result.get("solution", {}).get("gRecaptchaResponse")
                    logger.info(f"CapSolver solved: {task_id}")
                    return solution
                
                time.sleep(1)
            
            except Exception as e:
                logger.error(f"CapSolver get result error: {e}")
                return None
        
        logger.warning(f"CapSolver timeout for task {task_id}")
        return None


class TwoCaptchaService(CaptchaService):
    """2Captcha API integration"""
    
    BASE_URL = "https://2captcha.com"
    
    def solve(self, captcha_data: Dict[str, Any]) -> Optional[str]:
        """
        Solve captcha using 2Captcha
        captcha_data should contain: method, body (for image) or other type-specific params
        """
        try:
            # Submit captcha
            submit_url = f"{self.BASE_URL}/in.php"
            
            params = {
                "key": self.api_key,
                **captcha_data
            }
            
            response = requests.post(submit_url, data=params, timeout=self.timeout)
            response_text = response.text
            
            if response_text.startswith("OK|"):
                captcha_id = response_text.split("|")[1]
                logger.info(f"2Captcha submitted: {captcha_id}")
                
                # Poll for result
                return self._get_result(captcha_id)
            else:
                logger.error(f"2Captcha submit error: {response_text}")
                return None
        
        except Exception as e:
            logger.error(f"2Captcha error: {e}")
            return None
    
    def _get_result(self, captcha_id: str, max_attempts: int = 60) -> Optional[str]:
        """Poll 2Captcha for result"""
        get_url = f"{self.BASE_URL}/res.php"
        
        for attempt in range(max_attempts):
            try:
                params = {
                    "key": self.api_key,
                    "action": "get",
                    "id": captcha_id
                }
                
                response = requests.get(get_url, params=params, timeout=self.timeout)
                response_text = response.text
                
                if response_text.startswith("OK|"):
                    solution = response_text.split("|")[1]
                    logger.info(f"2Captcha solved: {captcha_id}")
                    return solution
                
                elif response_text == "CAPCHA_NOT_READY":
                    time.sleep(5)
                    continue
                
                else:
                    logger.error(f"2Captcha get error: {response_text}")
                    return None
            
            except Exception as e:
                logger.error(f"2Captcha get result error: {e}")
                return None
        
        logger.warning(f"2Captcha timeout for captcha {captcha_id}")
        return None


class NopechaService(CaptchaService):
    """NopeCHA API integration"""
    
    BASE_URL = "https://api.nopecha.com/api/v1"
    
    def solve(self, captcha_data: Dict[str, Any]) -> Optional[str]:
        """
        Solve captcha using NopeCHA
        captcha_data should contain: type, sitekey, url
        """
        try:
            # Submit captcha
            solve_url = f"{self.BASE_URL}/solve"
            
            payload = {
                "key": self.api_key,
                **captcha_data
            }
            
            response = requests.post(solve_url, json=payload, timeout=self.timeout)
            result = response.json()
            
            if result.get("status") == "solving":
                request_id = result.get("request_id")
                logger.info(f"NopeCHA submitted: {request_id}")
                
                # Poll for result
                return self._get_result(request_id)
            else:
                logger.error(f"NopeCHA submit error: {result}")
                return None
        
        except Exception as e:
            logger.error(f"NopeCHA error: {e}")
            return None
    
    def _get_result(self, request_id: str, max_attempts: int = 60) -> Optional[str]:
        """Poll NopeCHA for result"""
        get_url = f"{self.BASE_URL}/get_solution"
        
        for attempt in range(max_attempts):
            try:
                params = {
                    "id": request_id,
                    "key": self.api_key
                }
                
                response = requests.get(get_url, params=params, timeout=self.timeout)
                result = response.json()
                
                if result.get("status") == "solved":
                    solution = result.get("solution")
                    logger.info(f"NopeCHA solved: {request_id}")
                    return solution
                
                time.sleep(1)
            
            except Exception as e:
                logger.error(f"NopeCHA get result error: {e}")
                return None
        
        logger.warning(f"NopeCHA timeout for request {request_id}")
        return None


class AnticaptchaService(CaptchaService):
    """AntiCaptcha API integration"""
    
    BASE_URL = "https://api.anticaptcha.com"
    
    def solve(self, captcha_data: Dict[str, Any]) -> Optional[str]:
        """
        Solve captcha using AntiCaptcha
        captcha_data should contain: type, websiteURL, websiteKey, etc.
        """
        try:
            # Create task
            create_url = f"{self.BASE_URL}/createTask"
            payload = {
                "clientKey": self.api_key,
                "task": captcha_data
            }
            
            response = requests.post(create_url, json=payload, timeout=self.timeout)
            result = response.json()
            
            if not result.get("errorId") == 0:
                logger.error(f"AntiCaptcha create task error: {result}")
                return None
            
            task_id = result.get("taskId")
            logger.info(f"AntiCaptcha task created: {task_id}")
            
            # Poll for result
            return self._get_result(task_id)
        
        except Exception as e:
            logger.error(f"AntiCaptcha error: {e}")
            return None
    
    def _get_result(self, task_id: int, max_attempts: int = 60) -> Optional[str]:
        """Poll AntiCaptcha for result"""
        get_url = f"{self.BASE_URL}/getTaskResult"
        
        for attempt in range(max_attempts):
            try:
                payload = {
                    "clientKey": self.api_key,
                    "taskId": task_id
                }
                
                response = requests.post(get_url, json=payload, timeout=self.timeout)
                result = response.json()
                
                if result.get("isReady"):
                    solution = result.get("solution", {}).get("gRecaptchaResponse")
                    logger.info(f"AntiCaptcha solved: {task_id}")
                    return solution
                
                time.sleep(1)
            
            except Exception as e:
                logger.error(f"AntiCaptcha get result error: {e}")
                return None
        
        logger.warning(f"AntiCaptcha timeout for task {task_id}")
        return None


class DeathbycaptchaService(CaptchaService):
    """DeathByCaptcha API integration"""
    
    BASE_URL = "https://deathbycaptcha.com/api/captcha"
    
    def __init__(self, username: str, password: str, timeout: int = 60):
        self.username = username
        self.password = password
        self.timeout = timeout
    
    def solve(self, captcha_data: Dict[str, Any]) -> Optional[str]:
        """
        Solve captcha using DeathByCaptcha
        captcha_data should contain: captchafile (base64) or other image data
        """
        try:
            auth = (self.username, self.password)
            payload = captcha_data
            
            response = requests.post(
                self.BASE_URL,
                data=payload,
                auth=auth,
                timeout=self.timeout
            )
            result = response.json()
            
            if result.get("is_correct"):
                captcha_id = result.get("captcha")
                logger.info(f"DeathByCaptcha submitted: {captcha_id}")
                
                # Poll for result
                return self._get_result(captcha_id)
            else:
                logger.error(f"DeathByCaptcha submit error: {result}")
                return None
        
        except Exception as e:
            logger.error(f"DeathByCaptcha error: {e}")
            return None
    
    def _get_result(self, captcha_id: int, max_attempts: int = 60) -> Optional[str]:
        """Poll DeathByCaptcha for result"""
        get_url = f"{self.BASE_URL}/{captcha_id}"
        auth = (self.username, self.password)
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(get_url, auth=auth, timeout=self.timeout)
                result = response.json()
                
                if result.get("is_correct"):
                    solution = result.get("text")
                    logger.info(f"DeathByCaptcha solved: {captcha_id}")
                    return solution
                
                time.sleep(1)
            
            except Exception as e:
                logger.error(f"DeathByCaptcha get result error: {e}")
                return None
        
        logger.warning(f"DeathByCaptcha timeout for captcha {captcha_id}")
        return None


def get_service_instance(service_name: str, config: Dict[str, Any]) -> Optional[CaptchaService]:
    """Factory function to get captcha service instance"""
    
    try:
        if service_name == "capsolver":
            return CapSolverService(config["api_key"], config["timeout"])
        
        elif service_name == "2captcha":
            return TwoCaptchaService(config["api_key"], config["timeout"])
        
        elif service_name == "nopecha":
            return NopechaService(config["api_key"], config["timeout"])
        
        elif service_name == "anticaptcha":
            return AnticaptchaService(config["api_key"], config["timeout"])
        
        elif service_name == "deathbycaptcha":
            return DeathbycaptchaService(
                config["username"],
                config["password"],
                config["timeout"]
            )
        
        else:
            logger.error(f"Unknown service: {service_name}")
            return None
    
    except Exception as e:
        logger.error(f"Failed to create service instance for {service_name}: {e}")
        return None
