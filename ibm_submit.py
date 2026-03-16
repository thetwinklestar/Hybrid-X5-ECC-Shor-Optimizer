#!/usr/bin/env python3
"""
ibm_submit.py
IBM Quantum Hardware Submission Script - Q-Day Prize
English Version

Submit Shor+X5 optimized circuit to real IBM quantum computers.
"""

import argparse
import json
import sys
from datetime import datetime


def submit_to_ibm(backend_name='ibm_brisbane', key_file=None, shots=8192):
    """
    Submit X(5) optimized Shor algorithm circuit to IBM Quantum hardware.

    Args:
        backend_name: IBM backend name (ibm_brisbane, ibm_sherbrooke, ibm_kyoto)
        key_file: Official Q-Day Prize test key file (JSON format)
        shots: Number of measurement shots (default: 8192)
    """
    print("="*60)
    print("IBM Quantum Hardware Submission - Shor+X5 Optimized")
    print("="*60)
    print(f"Backend: {backend_name}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Load official test key if provided
    if key_file:
        try:
            with open(key_file) as f:
                key_data = json.load(f)
            print(f"[✓] Loaded official key: {key_file}")
            print(f"  Curve: {key_data.get('curve', 'secp256k1')}")
            print(f"  Bits: {key_data.get('bit_length', 'unknown')}")
        except Exception as e:
            print(f"[✗] Cannot load key file: {e}")
            key_data = None
    else:
        print("[i] No key file provided, using default 3-bit test parameters")
        key_data = None

    # Import and create circuit
    try:
        from ecc_x5_quantum import X5ECCAdder

        # Parameter setup
        if key_data and key_data.get('bit_length', 0) <= 25:
            p = key_data.get('base_field', 11)
            n_bits = key_data['bit_length']
            print(f"[✓] Using official test key parameters: {n_bits}bit")
        else:
            # Default 3-bit demonstration
            p = 11
            n_bits = 4
            print(f"[i] Using default 3-bit demo parameters (p={p})")

        # Golden ratio in F_p
        phi = 4 if p == 11 else find_golden_ratio(p)

        # Create Shor algorithm oracle circuit
        adder = X5ECCAdder(p=p, n_bits=n_bits, phi=phi)

        # Test scenario: G + 2G = 3G in Shor algorithm
        if p == 11:
            R1 = pow(phi, 3, p)  # G -> 9
            R2 = pow(phi, 6, p)  # 2G -> 4
            expected = pow(phi, 9, p)  # 3G -> 3

            print(f"\nTest Scenario: G + 2G = 3G (Shor scalar multiplication)")
            print(f"R1 = phi³ ≡ {R1} (mod {p})")
            print(f"R2 = phi⁶ ≡ {R2} (mod {p})")
            print(f"Expected = phi⁹ ≡ {expected} (mod {p})")

        # Create circuit
        circ = adder.create_adder_circuit(R1, R2)

        print(f"\nCircuit Statistics:")
        print(f"  Qubits: {circ.num_qubits}")
        print(f"  Depth: {circ.depth()}")
        print(f"  Total gates: {len(circ.data)}")

        # Attempt IBM submission
        print(f"\nConnecting to IBM Quantum backend: {backend_name}...")

        try:
            from qiskit_ibm_runtime import QiskitRuntimeService, Session, Sampler

            # Load IBM service (requires pre-configured token)
            service = QiskitRuntimeService()
            backend = service.backend(backend_name)

            print(f"[✓] Connected: {backend.name}")
            print(f"  Status: {backend.status().status_msg}")
            print(f"  Queue: {backend.status().pending_jobs}")

            # Optimize for hardware
            from qiskit import transpile
            optimized = transpile(circ, backend, optimization_level=3)

            print(f"\nHardware Optimized:")
            print(f"  Depth: {optimized.depth()}")
            print(f"  Gates: {len(optimized.data)}")

            # Submit job
            print(f"\nSubmitting job (shots={shots})...")

            with Session(backend=backend) as session:
                sampler = Sampler(session=session)
                job = sampler.run([optimized], shots=shots)

                job_id = job.job_id
                print(f"[✓] Job submitted! Job ID: {job_id}")
                print(f"\nSave this Job ID for Q-Day Prize submission proof:")
                print(f"  Job ID: {job_id}")
                print(f"  Backend: {backend_name}")
                print(f"  Shots: {shots}")
                print(f"  Timestamp: {datetime.now().isoformat()}")

                # Save submission record
                record = {
                    "job_id": job_id,
                    "backend": backend_name,
                    "shots": shots,
                    "timestamp": datetime.now().isoformat(),
                    "circuit_params": {
                        "p": p,
                        "n_bits": n_bits,
                        "phi": phi,
                        "R1": R1,
                        "R2": R2,
                        "expected": expected if p == 11 else None
                    }
                }

                filename = f'ibm_job_{job_id[:8]}.json'
                with open(filename, 'w') as f:
                    json.dump(record, f, indent=2)

                print(f"\n[✓] Submission record saved: {filename}")
                print(f"Include this Job ID in your Q-Day Prize submission email as hardware verification proof.")

                return job_id

        except Exception as e:
            print(f"\n[✗] IBM submission failed: {e}")
            print("\nPossible reasons:")
            print("  1. IBM Quantum API Token not configured")
            print("     Solution: python -c \"from qiskit_ibm_runtime import QiskitRuntimeService; \"")
            print("               QiskitRuntimeService.save_account(token='YOUR_TOKEN')\"")
            print("  2. Backend unavailable or queue full")
            print("  3. Network connectivity issue")
            print("\nYou can still:")
            print("  - Run local simulation: python run_full_pipeline.py")
            print("  - Use alternative backend: --backend ibm_sherbrooke")
            return None

    except ImportError as e:
        print(f"[✗] Import error: {e}")
        print("Ensure installed: pip install qiskit qiskit-ibm-runtime")
        return None


def find_golden_ratio(p):
    """Find golden ratio in F_p (satisfying phi² = phi + 1)"""
    for phi in range(2, p):
        if (phi * phi) % p == (phi + 1) % p:
            return phi
    raise ValueError(f"No golden ratio found in F_{p}")


def check_job_status(job_id):
    """Query status of submitted job"""
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService

        service = QiskitRuntimeService()
        job = service.job(job_id)

        print(f"Job ID: {job_id}")
        print(f"Status: {job.status()}")

        if job.status() == 'DONE':
            result = job.result()
            print(f"Result: {result}")

    except Exception as e:
        print(f"Query failed: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='IBM Quantum Hardware Submission - Q-Day Prize',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Submit 3-bit demo to ibm_brisbane
  python ibm_submit.py --backend ibm_brisbane

  # Use official test key (after downloading)
  python ibm_submit.py --backend ibm_sherbrooke --key official_5bit.json

  # Check submitted job status
  python ibm_submit.py --check-job cvt5xxxxx

Note:
  First-time use requires IBM Quantum API Token:
  python -c "from qiskit_ibm_runtime import QiskitRuntimeService; 
            QiskitRuntimeService.save_account(token='YOUR_TOKEN')"
        """
    )

    parser.add_argument('--backend', default='ibm_brisbane',
                       help='IBM Quantum backend name (default: ibm_brisbane)')
    parser.add_argument('--key', dest='key_file',
                       help='Official Q-Day Prize test key file (JSON format)')
    parser.add_argument('--shots', type=int, default=8192,
                       help='Number of measurement shots (default: 8192)')
    parser.add_argument('--check-job',
                       help='Check status of previously submitted job')

    args = parser.parse_args()

    if args.check_job:
        check_job_status(args.check_job)
    else:
        job_id = submit_to_ibm(args.backend, args.key_file, args.shots)

        if job_id:
            print("\n" + "="*60)
            print("Submission Successful!")
            print("Include this Job ID in your Q-Day Prize submission:")
            print(f"  Job ID: {job_id}")
            print("="*60)
        else:
            sys.exit(1)


if __name__ == '__main__':
    main()
