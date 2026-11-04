import { ExternalLink, WifiOff } from "lucide-react";

import { CopyButton } from "@/components";
import { copy } from "@/copy";
import { isEmbedded, storageAvailable } from "@/api/storage";
import { useAccessKey } from "@/api/useAccessKey";

import { useOnline } from "./useOnline";

function Banner({
  title,
  children,
  icon,
}: {
  title: string;
  children: React.ReactNode;
  icon: React.ReactNode;
}) {
  return (
    <div role="status" className="border-b border-hairline bg-wash">
      <div className="mx-auto flex max-w-[760px] items-start gap-3 px-4 py-3">
        <span aria-hidden="true" className="mt-0.5 shrink-0">
          {icon}
        </span>
        <div>
          <p className="font-bold">{title}</p>
          <div className="text-sm text-muted">{children}</div>
        </div>
      </div>
    </div>
  );
}

export function AppBanners() {
  const online = useOnline();
  const accessKey = useAccessKey();
  const embedded = isEmbedded();

  if (online && storageAvailable && !embedded) return null;

  return (
    <>
      {!online ? (
        <Banner title={copy.shell.offlineTitle} icon={<WifiOff size={18} />}>
          {copy.shell.offlineBody}
        </Banner>
      ) : null}
      {!storageAvailable ? (
        <Banner title={copy.shell.storageTitle} icon={<span aria-hidden="true">!</span>}>
          <p>{copy.shell.storageBody}</p>
          {accessKey ? (
            <div className="mt-2">
              <CopyButton value={accessKey} label={copy.shell.copyKey} variant="secondary" />
            </div>
          ) : null}
        </Banner>
      ) : null}
      {embedded ? (
        <Banner title={copy.shell.embeddedTitle} icon={<ExternalLink size={18} />}>
          <p>{copy.shell.embeddedBody}</p>
          <a
            href={window.location.href}
            target="_blank"
            rel="noreferrer"
            className="mt-1 inline-block font-bold"
          >
            {copy.shell.openNewTab}
          </a>
        </Banner>
      ) : null}
    </>
  );
}
