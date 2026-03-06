"""
API Key Generator Utility
Provides secure API key generation for authentication
"""
import secrets
import string


class APIKeyGenerator:
    """Utility class for generating secure API keys"""

    @staticmethod
    def generate_api_key(length: int = 32, prefix: str = "vaani") -> str:
        """
        Generate a cryptographically secure API key.

        Returns:
            str: Generated API key in format: prefix_randomstring
        """
        alphabet = string.ascii_lowercase + string.digits
        ambiguous_chars = '01lo'
        alphabet = ''.join(c for c in alphabet if c not in ambiguous_chars)
        random_part = ''.join(secrets.choice(alphabet) for _ in range(length))

        if prefix:
            return f"{prefix}_{random_part}"
        return random_part

    @staticmethod
    def generate_multiple_keys(count: int = 3, length: int = 32, prefix: str = "vaani") -> list[str]:
        """Generate multiple API keys at once."""
        return [APIKeyGenerator.generate_api_key(length, prefix) for _ in range(count)]


def main():
    """CLI tool to generate API keys"""
    print("\n" + "="*60)
    print("VAANI API KEY GENERATOR")
    print("="*60 + "\n")

    api_key = APIKeyGenerator.generate_api_key(length=32, prefix="vaani")

    print(f"Generated API Key:\n")
    print(f"  {api_key}\n")
    print("-"*60)
    print("\nAdd this to your .env file:")
    print(f"\n  VAANI_API_KEY={api_key}\n")
    print("-"*60)
    print("\nUse in API requests:")
    print(f'\n  curl -H "X-API-Key: {api_key}" ...\n')
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
