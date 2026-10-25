import "server-only";

// Only completed, independently verified maintenance receipts belong here.
// These links do not grant Drive access. The archive bytes and keys stay private.
export const ARCHIVE_OWNER_ID = 1;
export const ARCHIVES = [
  {
    id: "40203396058",
    date: "25 October 2026",
    snapshots: 265420,
    fields: 142392,
    legacyBackup: 0,
    snapshotBefore: "18 October 2026, 8:11 PM IST",
    fieldBefore: "24 October 2026, 8:11 PM IST",
    bytes: 38482358,
    sha256: "8e9b9817253205374295c5ebd8d722fff984982fcc0776a527c1d927a8223c75",
    driveUrl: "https://drive.google.com/file/d/1PowmjvnETZQdYaYzNVs74LRbQThXNsEV/view?usp=drivesdk",
  },
  {
    id: "38091428425",
    date: "11 October 2026",
    snapshots: 459403,
    fields: 0,
    legacyBackup: 191181,
    snapshotBefore: "4 October 2026, 3:56 AM IST",
    fieldBefore: null,
    bytes: 56674905,
    sha256: "fde0ced00f2676579299b7b6cfb7d3e291c8371b2a4ee129f55b9ed7685dcc2e",
    driveUrl: "https://drive.google.com/file/d/14zKL4p6mSGtJ9IRIT8vHsLgGUI79EQ_q/view?usp=drivesdk",
  },
] as const;

