"""
tools/diagnose_camera.py
Diagnostic tool for TOF camera via CSI port.

Run: python3 tools/diagnose_camera.py

Checks:
- Camera detection (libcamera)
- Picamera2 availability
- Depth data capture
- Frame rate
- Depth statistics
"""

import sys
import subprocess
import time

try:
    import numpy as np
    import cv2
except ImportError as e:
    print(f"✗ Missing dependency: {e}")
    print("  Install: pip install opencv-python numpy")
    sys.exit(1)


def check_vcgencmd():
    """Check if camera is detected by Raspberry Pi"""
    print("\n[1] Raspberry Pi Camera Detection")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            ['vcgencmd', 'get_camera'],
            capture_output=True,
            text=True
        )
        output = result.stdout.strip()
        print(f"vcgencmd: {output}")
        
        if "supported=1" in output and "detected=1" in output:
            print("✓ Camera detected and supported")
            return True
        else:
            print("✗ Camera not detected or not supported")
            print("  Run: sudo raspi-config → Interface Options → Camera → Enable")
            return False
            
    except FileNotFoundError:
        print("✗ vcgencmd not found (not on Raspberry Pi?)")
        return None


def check_libcamera():
    """Check libcamera availability"""
    print("\n[2] libcamera Support")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            ['libcamera-still', '--list-cameras'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("Available cameras:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"  {line}")
            
            if "arducam" in result.stdout.lower() or "tof" in result.stdout.lower():
                print("✓ ArduCAM TOF detected")
                return True
            else:
                print("⚠ Camera detected but may not be ArduCAM TOF")
                return True
        else:
            print("✗ libcamera-still failed")
            print(f"  Error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("✗ libcamera-still not found")
        print("  Install: sudo apt install -y libcamera-tools")
        return False
    except subprocess.TimeoutExpired:
        print("✗ libcamera-still timed out")
        return False


def check_picamera2():
    """Check Picamera2 availability"""
    print("\n[3] Picamera2 Library")
    print("-" * 50)
    
    try:
        from picamera2 import Picamera2
        print("✓ Picamera2 imported successfully")
        
        try:
            picam2 = Picamera2()
            print(f"✓ Picamera2 instance created")
            print(f"  Properties: {picam2.camera_properties()}")
            picam2 = None
            return True
        except Exception as e:
            print(f"⚠ Picamera2 import OK but instantiation failed: {e}")
            return False
            
    except ImportError:
        print("✗ Picamera2 not installed")
        print("  Install: sudo apt install -y python3-picamera2")
        return False


def check_camera_module():
    """Test actual camera module"""
    print("\n[4] SmartBin Camera Module")
    print("-" * 50)
    
    try:
        from src.camera_real import RealCamera
        from config.sim_settings import SimSettings
        
        settings = SimSettings()
        print(f"Settings loaded: {settings.FRAME_WIDTH}x{settings.FRAME_HEIGHT}")
        
        try:
            camera = RealCamera(settings=settings)
            print("✓ Camera initialized")
            
            # Try to capture
            print("  Capturing frames...")
            frames_ok = 0
            depths = []
            
            for i in range(5):
                depth = camera.get_depth_frame()
                if depth is not None:
                    frames_ok += 1
                    depths.append(depth)
                    print(f"    Frame {i+1}: {depth.shape} | "
                          f"range: {depth.min():.2f}m - {depth.max():.2f}m")
                else:
                    print(f"    Frame {i+1}: FAILED")
                time.sleep(0.2)
            
            camera.cleanup()
            
            if frames_ok > 0:
                print(f"✓ Captured {frames_ok}/5 frames successfully")
                
                # Stats
                all_depths = np.concatenate(depths)
                valid = all_depths > 0
                if np.any(valid):
                    vd = all_depths[valid]
                    print(f"  Overall depth range: {vd.min():.2f}m - {vd.max():.2f}m")
                    print(f"  Mean depth: {vd.mean():.2f}m")
                    print(f"  Std dev: {vd.std():.2f}m")
                
                return True
            else:
                print(f"✗ Could not capture any frames")
                return False
                
        except Exception as e:
            print(f"✗ Camera initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def main():
    print("=" * 50)
    print("SmartBin TOF Camera Diagnostic")
    print("=" * 50)
    
    results = {}
    
    # Run checks
    results['vcgencmd'] = check_vcgencmd()
    results['libcamera'] = check_libcamera()
    results['picamera2'] = check_picamera2()
    results['camera_module'] = check_camera_module()
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    for check, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL" if result is False else "⚠ WARN"
        print(f"{status}  {check}")
    
    if results['camera_module']:
        print("\n✓ All checks passed! Camera is ready.")
        print("Run: python3 tools/tune_tof.py")
        sys.exit(0)
    elif results['camera_module'] is False:
        print("\n✗ Camera module test failed.")
        print("Check error messages above and verify CSI connection.")
        sys.exit(1)
    else:
        print("\n⚠ Some checks failed. See details above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
