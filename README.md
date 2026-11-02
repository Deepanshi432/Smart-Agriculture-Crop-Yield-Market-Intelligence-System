* Column names aur values me extra spaces hain (`"District "`, `"Area "`, `"Kharif "`), `strip()` lagao.
* 4,948 rows me `Production` missing hai, 9 me `Crop` missing hai, aur 1,466 rows me Production 0 hai.
* Yield me outliers hain (max 43,958 jab median 1.0 hai), to unhe cap ya filter karo.
* State ke naam ki spelling alag hai: `Odisha` vs rainfall me `Orissa`, `CHANDIGARH`, `THE DADRA AND NAGAR HAVELI` aur `Dadra and Nagar Haveli` ek hi state hain.
* Crop ke alag units hain (nariyal jaise crops ka production nuts me hai), to Yield ko alag-alag crops me seedhe compare mat karo. pehle ye karte hai
