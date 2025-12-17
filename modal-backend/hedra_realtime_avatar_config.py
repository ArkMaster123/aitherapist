"""
Configuration and utility functions for Hedra Realtime Avatar setup.

This file provides:
- Environment variable validation
- Modal secrets configuration helpers
- Avatar image validation
- Connection testing utilities
"""

import os
from pathlib import Path
from typing import Optional, Dict
from PIL import Image


class HedraAvatarConfig:
    """Configuration manager for Hedra Realtime Avatar setup."""
    
    REQUIRED_ENV_VARS = [
        "LIVEKIT_WS_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "OPENAI_API_KEY",
    ]
    
    OPTIONAL_ENV_VARS = [
        "OPENAI_MODEL",  # Default: gpt-4o-realtime-preview
        "AVATAR_IDENTITY",  # Default: static-avatar
    ]
    
    @classmethod
    def validate_env_vars(cls, raise_on_missing: bool = True) -> Dict[str, bool]:
        """
        Validate that all required environment variables are set.
        
        Args:
            raise_on_missing: If True, raise ValueError on missing vars
            
        Returns:
            Dict mapping env var names to whether they're set
            
        Raises:
            ValueError: If raise_on_missing=True and any required var is missing
        """
        results = {}
        missing = []
        
        for var in cls.REQUIRED_ENV_VARS:
            is_set = var in os.environ and os.environ[var]
            results[var] = is_set
            if not is_set:
                missing.append(var)
        
        if missing and raise_on_missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Set them via Modal secrets or environment variables."
            )
        
        return results
    
    @classmethod
    def get_livekit_config(cls) -> Dict[str, str]:
        """Get LiveKit configuration from environment."""
        cls.validate_env_vars(raise_on_missing=True)
        
        return {
            "ws_url": os.environ["LIVEKIT_WS_URL"],
            "api_key": os.environ["LIVEKIT_API_KEY"],
            "api_secret": os.environ["LIVEKIT_API_SECRET"],
        }
    
    @classmethod
    def get_openai_config(cls) -> Dict[str, str]:
        """Get OpenAI configuration from environment."""
        cls.validate_env_vars(raise_on_missing=True)
        
        return {
            "api_key": os.environ["OPENAI_API_KEY"],
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-realtime-preview"),
        }
    
    @classmethod
    def get_avatar_identity(cls) -> str:
        """Get avatar participant identity."""
        return os.environ.get("AVATAR_IDENTITY", "static-avatar")


class AvatarImageLoader:
    """Utility for loading and validating avatar images."""
    
    SUPPORTED_FORMATS = (".png", ".jpg", ".jpeg")
    MAX_SIZE = (2048, 2048)  # Max dimensions
    MIN_SIZE = (256, 256)    # Min dimensions
    RECOMMENDED_SIZE = (512, 512)  # Recommended dimensions
    
    @classmethod
    def find_avatar_image(cls, base_dir: Optional[Path] = None) -> Path:
        """
        Find avatar image in directory.
        
        Searches for avatar.png, avatar.jpg, avatar.jpeg in order.
        
        Args:
            base_dir: Directory to search (default: script directory)
            
        Returns:
            Path to avatar image
            
        Raises:
            FileNotFoundError: If no avatar image found
        """
        if base_dir is None:
            # Default to directory containing this file
            base_dir = Path(__file__).resolve().parent
        
        for ext in cls.SUPPORTED_FORMATS:
            candidate = base_dir / f"avatar{ext}"
            if candidate.exists():
                return candidate
        
        formats_list = [f"avatar{ext}" for ext in cls.SUPPORTED_FORMATS]
        raise FileNotFoundError(
            f"No avatar image found in {base_dir}\n"
            f"Expected one of: {formats_list}"
        )
    
    @classmethod
    def validate_avatar_image(cls, image_path: Path) -> Dict[str, any]:
        """
        Validate avatar image meets requirements.
        
        Args:
            image_path: Path to avatar image
            
        Returns:
            Dict with validation results:
            - valid: bool
            - width: int
            - height: int
            - format: str
            - size_mb: float
            - warnings: List[str]
            
        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If image is invalid format
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Avatar image not found: {image_path}")
        
        results = {
            "valid": True,
            "warnings": [],
            "path": str(image_path),
        }
        
        try:
            with Image.open(image_path) as img:
                results["width"] = img.width
                results["height"] = img.height
                results["format"] = img.format
                results["mode"] = img.mode
                
                # Check file size
                file_size_mb = image_path.stat().st_size / (1024 * 1024)
                results["size_mb"] = file_size_mb
                
                # Validate dimensions
                if img.width < cls.MIN_SIZE[0] or img.height < cls.MIN_SIZE[1]:
                    results["warnings"].append(
                        f"Image is smaller than recommended minimum {cls.MIN_SIZE}"
                    )
                
                if img.width > cls.MAX_SIZE[0] or img.height > cls.MAX_SIZE[1]:
                    results["warnings"].append(
                        f"Image exceeds maximum {cls.MAX_SIZE}, may cause performance issues"
                    )
                
                # Check aspect ratio (square is best)
                aspect_ratio = img.width / img.height
                if abs(aspect_ratio - 1.0) > 0.1:
                    results["warnings"].append(
                        f"Aspect ratio {aspect_ratio:.2f} is not square (1:1 recommended)"
                    )
                
                # Check file size
                if file_size_mb > 2.0:
                    results["warnings"].append(
                        f"File size {file_size_mb:.2f}MB is large, consider compressing"
                    )
                
                # Check format
                if img.format not in ("PNG", "JPEG"):
                    results["valid"] = False
                    results["warnings"].append(
                        f"Format {img.format} may not be optimal (PNG/JPEG recommended)"
                    )
                
                # Check mode (RGBA for PNG is good)
                if img.format == "PNG" and img.mode != "RGBA":
                    results["warnings"].append(
                        "PNG image should use RGBA mode for transparency support"
                    )
        
        except Exception as e:
            results["valid"] = False
            results["error"] = str(e)
        
        return results
    
    @classmethod
    def load_avatar_image(cls, base_dir: Optional[Path] = None) -> Image.Image:
        """
        Load and validate avatar image.
        
        Args:
            base_dir: Directory to search for avatar
            
        Returns:
            PIL Image object
            
        Raises:
            FileNotFoundError: If image not found
            ValueError: If image validation fails
        """
        image_path = cls.find_avatar_image(base_dir)
        validation = cls.validate_avatar_image(image_path)
        
        if not validation["valid"]:
            raise ValueError(
                f"Avatar image validation failed: {validation.get('error', 'Unknown error')}"
            )
        
        if validation["warnings"]:
            print("Avatar image warnings:")
            for warning in validation["warnings"]:
                print(f"  ⚠️  {warning}")
        
        return Image.open(image_path)


def print_config_status():
    """Print current configuration status (for debugging)."""
    print("=" * 60)
    print("Hedra Realtime Avatar Configuration Status")
    print("=" * 60)
    
    # Check environment variables
    print("\n📋 Environment Variables:")
    env_status = HedraAvatarConfig.validate_env_vars(raise_on_missing=False)
    for var, is_set in env_status.items():
        status = "✅" if is_set else "❌"
        value_preview = os.environ.get(var, "")[:20] + "..." if is_set else "not set"
        print(f"  {status} {var}: {value_preview}")
    
    # Check avatar image
    print("\n🖼️  Avatar Image:")
    try:
        image_path = AvatarImageLoader.find_avatar_image()
        validation = AvatarImageLoader.validate_avatar_image(image_path)
        print(f"  ✅ Found: {validation['path']}")
        print(f"     Size: {validation['width']}x{validation['height']}")
        print(f"     Format: {validation['format']}")
        print(f"     File size: {validation['size_mb']:.2f}MB")
        if validation["warnings"]:
            print(f"     ⚠️  {len(validation['warnings'])} warnings")
    except FileNotFoundError as e:
        print(f"  ❌ {e}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Configuration summary
    print("\n⚙️  Configuration Summary:")
    try:
        livekit_config = HedraAvatarConfig.get_livekit_config()
        openai_config = HedraAvatarConfig.get_openai_config()
        print(f"  ✅ LiveKit WS URL: {livekit_config['ws_url']}")
        print(f"  ✅ OpenAI Model: {openai_config['model']}")
        print(f"  ✅ Avatar Identity: {HedraAvatarConfig.get_avatar_identity()}")
    except ValueError as e:
        print(f"  ❌ Configuration incomplete: {e}")
    
    print("=" * 60)


if __name__ == "__main__":
    # When run directly, print config status
    print_config_status()

