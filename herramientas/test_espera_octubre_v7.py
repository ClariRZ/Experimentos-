"""Connection retries: timeouts, boot refusal, success and bounded failure."""
import subprocess
import unittest
from unittest.mock import Mock, patch
from continuar_octubre_v7 import wait_for_ssh

class ConnectionTests(unittest.TestCase):
    @patch('continuar_octubre_v7.time.sleep')
    def test_timeout_then_refusal_then_success(self, sleep):
        ssh=Mock(side_effect=[subprocess.TimeoutExpired('ssh',45),
            subprocess.CompletedProcess('ssh',255,'','Connection refused'),
            subprocess.CompletedProcess('ssh',0,'','')])
        wait_for_ssh(ssh,attempts=3)
        self.assertEqual(ssh.call_count,3)
        self.assertEqual(sleep.call_count,2)

    @patch('continuar_octubre_v7.time.sleep')
    def test_exhaustion_is_bounded(self,sleep):
        ssh=Mock(side_effect=subprocess.TimeoutExpired('ssh',45))
        with self.assertRaisesRegex(RuntimeError,'bounded retries'):
            wait_for_ssh(ssh,attempts=3)
        self.assertEqual(ssh.call_count,3)
        self.assertEqual(sleep.call_count,2)

    @patch('continuar_octubre_v7.time.sleep')
    def test_immediate_success(self,sleep):
        ssh=Mock(return_value=subprocess.CompletedProcess('ssh',0,'',''))
        wait_for_ssh(ssh)
        self.assertEqual(ssh.call_count,1)
        sleep.assert_not_called()

if __name__=='__main__':unittest.main()
