"""
=============================================================================
CRC (Cyclic Redundancy Check) Implementation Module
Hospital Laboratory Report Integrity Verification System
=============================================================================
Author: Educational Lab Project
Purpose: Manual implementation of CRC (Cyclic Redundancy Check) algorithm
         without third-party black-box libraries.
Algorithms:
  - CRC-16-CCITT (Polynomial: x^16 + x^12 + x^5 + 1 -> 0x1021)
  - CRC-8 (Polynomial: x^8 + x^2 + x + 1 -> 0x07 / 0x107)

How CRC Works (Modulo-2 Binary Division):
  1. The input message string is converted into a binary bitstream (ASCII).
  2. 'r' zeros are appended to the bitstream (where r is the polynomial degree).
  3. The padded bitstream is divided by the generator polynomial using
     Modulo-2 division (where XOR is used instead of arithmetic subtraction).
  4. The remainder left after division is the CRC checksum.
  5. If even a single bit in the message changes during transmission, the
     modulo-2 division yields a completely different remainder.
=============================================================================
"""

# Standard Generator Polynomials
POLYNOMIALS = {
    "CRC-16": {
        "name": "CRC-16-CCITT",
        "degree": 16,
        "poly_hex": "0x1021",
        # Full 17-bit divisor: 1 0001 0000 0010 0001
        "divisor_bits": "10001000000100001",
        "poly_int": 0x1021,
        "description": "Standard CRC-16 polynomial: x^16 + x^12 + x^5 + 1"
    },
    "CRC-8": {
        "name": "CRC-8-ATM",
        "degree": 8,
        "poly_hex": "0x07",
        # Full 9-bit divisor: 1 0000 0111
        "divisor_bits": "100000111",
        "poly_int": 0x07,
        "description": "Standard CRC-8 polynomial: x^8 + x^2 + x + 1"
    }
}


def string_to_binary(data_str: str) -> str:
    """
    Converts an input string into its 8-bit ASCII binary representation.
    Example: 'A' -> '01000001'
    """
    if not data_str:
        return "00000000"
    return "".join(format(ord(char), "08b") for char in data_str)


def xor_bits(a: str, b: str) -> str:
    """
    Performs bitwise XOR between two binary strings of equal length.
    Modulo-2 addition/subtraction rule:
      0 ^ 0 = 0
      0 ^ 1 = 1
      1 ^ 0 = 1
      1 ^ 1 = 0
    """
    result = []
    for bit_a, bit_b in zip(a, b):
        result.append("1" if bit_a != bit_b else "0")
    return "".join(result)


def modulo2_divide(dividend_bits: str, divisor_bits: str) -> tuple[str, list[dict]]:
    """
    Performs manual Modulo-2 binary long division using bitwise XOR.
    
    Args:
        dividend_bits: Padded message bit string (e.g., '0100000100000000')
        divisor_bits: Generator polynomial bit string (e.g., '100000111')
        
    Returns:
        remainder: The final remainder bit string of length (len(divisor) - 1)
        steps: List of division steps recorded for visual demonstration
    """
    divisor_len = len(divisor_bits)
    dividend_len = len(dividend_bits)
    
    # We strip any leading zeros from the start to find the first '1'
    # but keep full track of positions
    steps = []
    
    # Work on a mutable list of bits
    curr_bits = list(dividend_bits)
    
    # Step tracker
    step_num = 0
    max_recorded_steps = 30  # Cap step recording to prevent huge lists for long text
    
    for i in range(dividend_len - divisor_len + 1):
        if curr_bits[i] == "1":
            # XOR the divisor starting at current position
            window = "".join(curr_bits[i:i + divisor_len])
            xor_result = xor_bits(window, divisor_bits)
            
            # Record step if within limit
            if step_num < max_recorded_steps:
                steps.append({
                    "step": step_num + 1,
                    "position": i,
                    "current_window": window,
                    "divisor": divisor_bits,
                    "xor_result": xor_result,
                    "remainder_so_far": "".join(curr_bits[i + 1:i + divisor_len]) + "".join(curr_bits[i + divisor_len:min(i + divisor_len + 4, dividend_len)])
                })
                step_num += 1
                
            # Place XOR result back into curr_bits
            for j in range(divisor_len):
                curr_bits[i + j] = xor_result[j]
        else:
            # If current leading bit is 0, we simply shift forward (divide by 0)
            pass
            
    # Remainder is the last (divisor_len - 1) bits
    remainder = "".join(curr_bits[-(divisor_len - 1):])
    return remainder, steps


def calculate_crc(data: str, poly_type: str = "CRC-16") -> dict:
    """
    Calculates the CRC checksum for a given string using manual bitwise modulo-2 division.
    
    Args:
        data: The input string (e.g., serialized laboratory report)
        poly_type: 'CRC-16' or 'CRC-8'
        
    Returns:
        dict containing:
          - crc_hex: Hexadecimal string representation (e.g., '0x4F2A' or '0x8C')
          - crc_binary: Binary string of the remainder
          - crc_int: Integer value of CRC
          - polynomial: Name of the polynomial used
          - degree: Bit degree of polynomial (8 or 16)
          - input_length: Number of characters in input
    """
    if poly_type not in POLYNOMIALS:
        poly_type = "CRC-16"
        
    poly_info = POLYNOMIALS[poly_type]
    degree = poly_info["degree"]
    divisor_bits = poly_info["divisor_bits"]
    
    # 1. Convert data to binary bitstring
    raw_binary = string_to_binary(data)
    
    # 2. Append 'degree' zeros (r zeros) to the data stream
    padded_binary = raw_binary + ("0" * degree)
    
    # 3. Perform Modulo-2 division
    remainder_bits, _ = modulo2_divide(padded_binary, divisor_bits)
    
    # 4. Format the output
    crc_int = int(remainder_bits, 2) if remainder_bits else 0
    hex_format = f"0x{crc_int:0{degree // 4}X}"
    
    return {
        "crc_hex": hex_format,
        "crc_binary": remainder_bits,
        "crc_int": crc_int,
        "polynomial": poly_info["name"],
        "poly_hex": poly_info["poly_hex"],
        "degree": degree,
        "input_length": len(data),
        "raw_binary_sample": raw_binary[:64] + ("..." if len(raw_binary) > 64 else "")
    }


def get_crc_step_trace(data: str, poly_type: str = "CRC-8", max_steps: int = 25) -> dict:
    """
    Generates a detailed, student-friendly visual trace of the CRC calculation.
    Ideal for the interactive CRC Demonstration page and viva examination.
    """
    if poly_type not in POLYNOMIALS:
        poly_type = "CRC-8"
        
    poly_info = POLYNOMIALS[poly_type]
    degree = poly_info["degree"]
    divisor_bits = poly_info["divisor_bits"]
    
    # Limit data length for step tracing to avoid overwhelming browser UI
    truncated = False
    display_data = data
    if len(data) > 6:
        display_data = data[:6]
        truncated = True
        
    raw_binary = string_to_binary(display_data)
    padded_binary = raw_binary + ("0" * degree)

    # Character-by-character ASCII and binary breakdown
    char_breakdown = [
        {
            "char": c,
            "ascii": ord(c),
            "binary": format(ord(c), "08b")
        }
        for c in display_data
    ]
    
    remainder_bits, steps = modulo2_divide(padded_binary, divisor_bits)
    crc_int = int(remainder_bits, 2) if remainder_bits else 0
    hex_format = f"0x{crc_int:0{degree // 4}X}"
    
    return {
        "original_input": data,
        "analyzed_text": display_data,
        "is_truncated_for_trace": truncated,
        "char_breakdown": char_breakdown,
        "polynomial_name": poly_info["name"],
        "poly_hex": poly_info["poly_hex"],
        "divisor_bits": divisor_bits,
        "degree": degree,
        "raw_binary": raw_binary,
        "padded_binary": padded_binary,
        "zeros_appended": degree,
        "steps": steps[:max_steps],
        "total_steps_count": len(steps),
        "final_remainder_bits": remainder_bits,
        "final_crc_hex": hex_format,
        "final_crc_int": crc_int
    }


# Quick verification self-test if run directly
if __name__ == "__main__":
    print("--- CRC Manual Implementation Test ---")
    sample_text = "Blood Glucose: 95 mg/dL"
    res16 = calculate_crc(sample_text, "CRC-16")
    res8 = calculate_crc(sample_text, "CRC-8")
    
    print(f"Original Text: '{sample_text}'")
    print(f"CRC-16 Result: {res16['crc_hex']} (Binary: {res16['crc_binary']})")
    print(f"CRC-8  Result: {res8['crc_hex']} (Binary: {res8['crc_binary']})")
    
    # Corrupt single character: '95' -> '96'
    corrupted_text = "Blood Glucose: 96 mg/dL"
    res16_corrupt = calculate_crc(corrupted_text, "CRC-16")
    print(f"\nCorrupted Text: '{corrupted_text}'")
    print(f"Corrupted CRC-16: {res16_corrupt['crc_hex']}")
    print(f"Match? {res16['crc_hex'] == res16_corrupt['crc_hex']} (Expected: False)")
