/* 核心功能：导出前端离线兜底所需的官方赛程数据与元信息，供 API 失败或本地开发时使用。 */
import { officialScheduleMetadata, officialSchedulePayload } from "./official-schedule.js";

export const fallbackMatchesPayload = officialSchedulePayload;
export const fallbackScheduleMetadata = officialScheduleMetadata;

export function cloneFallbackPayload() {
  return JSON.parse(JSON.stringify(fallbackMatchesPayload));
}
