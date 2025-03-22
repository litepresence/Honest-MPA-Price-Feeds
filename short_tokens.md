
### Understanding **HONEST.USD** and **HONEST.USDSHORT** on BitShares: Two Powerful Margin Options for Traders

BitShares has introduced a new and innovative approach to trading stablecoins with **HONEST.USD** and **HONEST.USDSHORT**, two proprietary assets owned by the account `honest_quorum` on the BitShares network. These assets offer unique margin trading options, giving you the ability to **long** or **short** the price of BTS (BitShares) in a way that maintains flexibility and control.

Here’s a simple breakdown of how **HONEST.USD** and **HONEST.USDSHORT** work, and how they differ from each other:

### 1. **HONEST.USD (Long Position)**
**HONEST.USD** is a stablecoin pegged to the value of the U.S. dollar, but with a unique twist. To issue **HONEST.USD**, you use BTS (BitShares) as collateral, and the price of **HONEST.USD** is dynamically tied to the value of BTS through an oracle price feed. The key difference here is that you’re **going long** on BTS — in other words, you're betting that BTS will hold or increase in value.

#### How It Works:
- You lock up **BTS** as collateral in a **Collateralized Debt Position (CDP)**.
- The amount of **BTS** you need to lock up depends on the **oracle price feed** for BTS, which determines how much **HONEST.USD** you can issue.
- For example, if you lock up $200 worth of BTS, you can issue $100 worth of **HONEST.USD** (based on the collateralization ratio).
- If BTS rises in value, your **HONEST.USD** remains pegged to the USD, and you can repay the debt at a favorable rate.
- If BTS falls too much, you’ll face a **liquidation** risk — your collateral will be automatically sold to cover the debt.

#### Key Feature:
- **Going long on BTS** — you profit if BTS holds value or increases in price.
  
---

### 2. **HONEST.USDSHORT (Short Position)**
**HONEST.USDSHORT** is the inverse of **HONEST.USD**. It's designed for traders who want to take a **short position** on BTS — in other words, you’re betting that BTS will fall in price. Instead of directly pegging to the USD, the price of **HONEST.USDSHORT** is derived from the **inverse of the oracle price feed** for BTS.

#### How It Works:
- You lock up **BTS** as collateral, just like with **HONEST.USD**, but the issued asset (**HONEST.USDSHORT**) behaves differently.
- The value of **HONEST.USDSHORT** increases when the price of BTS falls, and decreases when BTS rises. This means you're **betting against BTS** — you profit if BTS decreases in value.
- If BTS rises instead of falling, you’ll need to repay the short position, but you face liquidation risk if your collateral isn’t enough to cover your short.

#### Key Feature:
- **Going short on BTS** — you profit if BTS decreases in value.

---

### Quick Comparison: **HONEST.USD** vs **HONEST.USDSHORT**

| Feature                        | **HONEST.USD (Long)**                      | **HONEST.USDSHORT (Short)**              |
|--------------------------------|-------------------------------------------|-----------------------------------------|
| **Collateral**                 | BTS (BitShares)                           | BTS (BitShares)                         |
| **Position Type**              | Long (betting that BTS price will rise)   | Short (betting that BTS price will fall)|
| **Price Feed**                 | Pegged to the value of USD through the **oracle price feed** | Pegged to the inverse of the BTS price through the **oracle price feed** |
| **Collateralization Ratio**    | Based on oracle price and risk management | Based on oracle price and risk management |
| **Profit Potential**           | Profits when BTS increases in value       | Profits when BTS decreases in value     |
| **Risk**                       | Risk of BTS price falling (liquidation risk if BTS value drops significantly) | Risk of BTS price rising (liquidation risk if BTS value rises significantly) |
| **Ideal For**                  | Traders who believe BTS will hold value or appreciate | Traders who believe BTS will decrease in value |

---

### Why Choose **HONEST.USD** or **HONEST.USDSHORT**?

- **Leverage Flexibility**: Both **HONEST.USD** and **HONEST.USDSHORT** allow you to trade with leverage, enabling you to amplify your potential returns (or losses).
- **Stablecoin Peg**: **HONEST.USD** is pegged to the U.S. dollar, making it an ideal option for those looking to hold a stable asset, while **HONEST.USDSHORT** allows you to speculate on the decline of BTS.
- **No Centralized Control**: These assets are decentralized, controlled by the **honest_quorum** account on BitShares, and governed by smart contracts.
- **Lower Fees**: As assets on the BitShares network, **HONEST.USD** and **HONEST.USDSHORT** benefit from BitShares' low transaction fees, making them an efficient way to enter leveraged positions.

---

### A Real-World Example:

#### Example 1: **HONEST.USD (Long Position)**

Let’s say you believe the value of BTS will rise and you want to take a long position by issuing **HONEST.USD**.

- **You lock up $200 worth of BTS**.
- The oracle price feed indicates that the price of BTS is $10, so you issue **$100 worth of HONEST.USD**.
- If the price of BTS increases to $20, the value of your collateral grows, but the **HONEST.USD** stays pegged to $1, maintaining stability.
- You can redeem your **HONEST.USD** for BTS at any time, but if the price of BTS drops below a certain level, liquidation will occur to protect the system.

#### Example 2: **HONEST.USDSHORT (Short Position)**

Now, let’s say you believe BTS will decrease in value and want to issue **HONEST.USDSHORT**.

- **You lock up $200 worth of BTS**.
- The oracle price feed indicates that the price of BTS is $10, so you issue **$100 worth of HONEST.USDSHORT**.
- If the price of BTS drops to $5, the value of **HONEST.USDSHORT** increases (from 1/10 = 0.10 to 1/5 = 0.20), meaning you make a profit.
- If BTS rises instead, the value of **HONEST.USDSHORT** will fall, and you will face liquidation risk if your collateral falls below the necessary collateralization ratio.

---

### Final Thoughts:

The **HONEST.USD** and **HONEST.USDSHORT** assets give BitShares users the ability to profit from both **rising and falling BTS prices**, all while providing stability through **oracle-backed price feeds**. Whether you're looking to **go long** with **HONEST.USD** or **bet against BTS** with **HONEST.USDSHORT**, these assets offer exciting opportunities to diversify your portfolio and increase your exposure in the market.

**Join the future of decentralized margin trading today with HONEST.USD and HONEST.USDSHORT!**