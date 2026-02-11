# Chapter 3 Memory System

## 3.1 Cache Organization

Caches organize copies of data into cache blocks, each of which represents a contiguous, naturally aligned power-of-two (or NAPOT) range of memory locations. The capacity and organization of a cache and the size of a cache block are both implementation-specific.

The cache hierarchy may include multiple levels (L1, L2, L3), with each level having different capacity and latency characteristics. The number of cache levels is implementation-defined.

## 3.2 CSR Address Space

The standard RISC-V ISA sets aside a 12-bit encoding space for up to 4,096 CSRs. By convention, the upper 4 bits of the CSR address are used to encode the read and write accessibility.

The mstatus register is a machine-mode CSR at address 0x300 that tracks and controls the hart's current operating state.

## 3.3 Vector Extension

The vector extension defines the VLEN parameter, which specifies the number of bits in a single vector register. VLEN must be a power of 2 and is implementation-defined, with a minimum value of 128 bits.

Vector registers are organized into groups, with the number of registers per group being implementation-specific.
