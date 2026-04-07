# evals/test_cases.py

TEST_CASES = [
    {
        "name": "password reset FAQ",
        "input": "How do I reset my password?",
        "expected_request_type": "safe",
        "expected_action": "none",
        "expected_sources": ["account_management.md"],
    },
    {
        "name": "annual refund within policy window",
        "input": "Can I get a refund for my annual plan after 10 days?",
        "expected_request_type": "sensitive",
        "expected_action": "approve_needed",
        "expected_sources": ["refund_policy.md"],
    },
    {
        "name": "cancellation plus refund",
        "input": "Cancel my account and refund me.",
        "expected_request_type": "sensitive",
        "expected_action": "approve_needed",
        "expected_sources": ["cancellation_policy.md", "refund_policy.md"],
    },
    {
        "name": "shipment compensation request",
        "input": "My shipment is delayed. Can you compensate me?",
        "expected_request_type": "sensitive",
        "expected_action": "approve_needed",
        "expected_sources": ["shipping_faq.md"],
    },
    {
        "name": "refund exception request",
        "input": "I want an exception to the refund policy because I am unhappy.",
        "expected_request_type": "requires_human",
        "expected_action": "escalate",
        "expected_sources": ["refund_policy.md"],
    },
    {
        "name": "paypal support",
        "input": "Do you support PayPal?",
        "expected_request_type": "safe",
        "expected_action": "none",
        "expected_sources": ["billing_faq.md"],
    },
]