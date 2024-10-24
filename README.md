# MPTCP Performance Optimization

## Project Overview
This project focuses on the performance optimization of MultiPath TCP (MPTCP) in different network conditions. We analyze how factors such as bandwidth, congestion control algorithms (Cubic vs. Reno), and packet loss rates affect data transmission efficiency and stability. The experiments are conducted in a simulated network environment using Mininet and Wireshark.

## Key Features
- **Virtual Network Setup:** Created using Mininet, simulating real-world conditions with varying bandwidth and packet loss.
- **Congestion Control Algorithms:** Comparison of Cubic and Reno algorithms in handling network congestion and their effect on data transfer.
- **Data Analysis:** Wireshark used for packet analysis to monitor network performance under different conditions.
- **Simulation Parameters:** Experiments included configurations of equal and unequal bandwidth, and 10% packet loss rate.

## Results Summary
- **Cubic Algorithm:** Exhibited stable performance in high-bandwidth scenarios but showed higher packet loss.
- **Reno Algorithm:** Reduced packet loss by 2% under 10% loss conditions but increased RTT by 4x.

## Tools & Technologies
- **Mininet** for virtual network creation.
- **Wireshark** for network traffic analysis.
- **Python** for scripting and network simulation control.
- **Linux Tools:** `tc` and `netem` for precise control over network parameters like bandwidth and packet loss.

## Future Work
- Extend the study to include more advanced congestion control algorithms such as BBR.
- Explore real-world MPTCP performance in dynamic mobile network environments.

## Contributors
- Hengshou Zhang - hzhan402@ucr.edu
- Zelai Fang - zfang052@ucr.edu